from time import time
from requests import post
from base64 import b64encode
from json import dumps

from flask import abort, request, current_app, Flask

from CTFd.cache import clear_challenges, clear_standings
from CTFd.models import Challenges
from CTFd.models import Fails, Solves
from CTFd.plugins.challenges import get_chal_class
from CTFd.utils import config, get_config
from CTFd.utils import user as current_user
from CTFd.utils.dates import ctf_paused, ctftime
from CTFd.utils.decorators import (
    during_ctf_time_only,
    require_verified_emails,
)
from CTFd.utils.decorators.visibility import (
    check_challenge_visibility,
)
from CTFd.utils.logging import log
from CTFd.utils.user import (
    authed,
    get_current_team,
    get_current_user,
)


@check_challenge_visibility
@during_ctf_time_only
@require_verified_emails
def attempt_hooked():
    if authed() is False:
        return {"success": True, "data": {"status": "authentication_required"}}, 403

    if request.content_type != "application/json":
        request_data = request.form
    else:
        request_data = request.get_json()

    challenge_id = request_data.get("challenge_id")

    if current_user.is_admin():
        preview = request.args.get("preview", False)
        if preview:
            challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
            chal_class = get_chal_class(challenge.type)
            status, message = chal_class.attempt(challenge, request)

            return {
                "success": True,
                "data": {
                    "status": "correct" if status else "incorrect",
                    "message": message,
                },
            }

    if ctf_paused():
        return (
            {
                "success": True,
                "data": {
                    "status": "paused",
                    "message": "{} is paused".format(config.ctf_name()),
                },
            },
            403,
        )

    user = get_current_user()
    team = get_current_team()

    # TODO: Convert this into a re-useable decorator
    if config.is_teams_mode() and team is None:
        abort(403)

    fails = Fails.query.filter_by(
        account_id=user.account_id, challenge_id=challenge_id
    ).count()

    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()

    if challenge.state == "hidden":
        abort(404)

    if challenge.state == "locked":
        abort(403)

    if challenge.requirements:
        requirements = challenge.requirements.get("prerequisites", [])
        solve_ids = (
            Solves.query.with_entities(Solves.challenge_id)
            .filter_by(account_id=user.account_id)
            .order_by(Solves.challenge_id.asc())
            .all()
        )
        solve_ids = {solve_id for solve_id, in solve_ids}
        # Gather all challenge IDs so that we can determine invalid challenge prereqs
        all_challenge_ids = {
            c.id for c in Challenges.query.with_entities(Challenges.id).all()
        }
        prereqs = set(requirements).intersection(all_challenge_ids)
        if solve_ids >= prereqs:
            pass
        else:
            abort(403)

    chal_class = get_chal_class(challenge.type)

    # Anti-bruteforce / submitting Flags too quickly
    kpm = current_user.get_wrong_submissions_per_minute(user.account_id)
    kpm_limit = int(get_config("incorrect_submissions_per_min", default=10))
    if kpm > kpm_limit:
        if ctftime():
            chal_class.fail(
                user=user, team=team, challenge=challenge, request=request
            )
        log(
            "submissions",
            "[{date}] {name} submitted {submission} on {challenge_id} with kpm {kpm} [TOO FAST]",
            name=user.name,
            submission=request_data.get("submission", "").encode("utf-8"),
            challenge_id=challenge_id,
            kpm=kpm,
        )
        # Submitting too fast
        return (
            {
                "success": True,
                "data": {
                    "status": "ratelimited",
                    "message": "You're submitting flags too fast. Slow down.",
                },
            },
            429,
        )

    solves = Solves.query.filter_by(
        account_id=user.account_id, challenge_id=challenge_id
    ).first()

    # Challenge not solved yet
    if not solves:
        # Hit max attempts
        max_tries = challenge.max_attempts
        if max_tries and fails >= max_tries > 0:
            return (
                {
                    "success": True,
                    "data": {
                        "status": "incorrect",
                        "message": "You have 0 tries remaining",
                    },
                },
                403,
            )

        status, message = chal_class.attempt(challenge, request)
        if status:  # The challenge plugin says the input is right
            header = {
                "HookToken": current_app.config["WEBHOOK_SESSION_TOKEN"]
            }
            if ctftime() or current_user.is_admin():
                chal_class.solve(
                    user=user, team=team, challenge=challenge, request=request
                )
                clear_standings()
                clear_challenges()

            solve_count = Solves.query.filter_by(challenge_id=challenge_id).count()
            data = {
                "challenge": challenge.name,
                "username": user.name,
                "time": round(time()),
                "count": solve_count
            }
            param = b64encode(dumps(data).encode()).decode()
            log(
                "submissions",
                "[{date}] {name} submitted {submission} on {challenge_id} with kpm {kpm} [CORRECT]",
                name=user.name,
                submission=request_data.get("submission", "").encode("utf-8"),
                challenge_id=challenge_id,
                kpm=kpm,
            )
            try:
                resp = post(
                    current_app.config["SUBMISSION_WEBHOOK_URL"].strip("/") + f"?data={param}",
                    headers=header, timeout=(5, 2)
                )
                log(
                    "webhook",
                    "[{time}] {name} submitted {submission} webhook status {status}",
                    time=data["time"],
                    name=data["username"],
                    submission=request_data.get("submission", "").encode("utf-8"),
                    status=resp.status_code
                )
            except Exception as e:
                log("webhook", "[error] {error}", error=str(e))
                pass
            return {
                "success": True,
                "data": {"status": "correct", "message": message},
            }
        else:  # The challenge plugin says the input is wrong
            if ctftime() or current_user.is_admin():
                chal_class.fail(
                    user=user, team=team, challenge=challenge, request=request
                )
                clear_standings()
                clear_challenges()

            log(
                "submissions",
                "[{date}] {name} submitted {submission} on {challenge_id} with kpm {kpm} [WRONG]",
                name=user.name,
                submission=request_data.get("submission", "").encode("utf-8"),
                challenge_id=challenge_id,
                kpm=kpm,
            )

            if max_tries:
                # Off by one since fails has changed since it was gotten
                attempts_left = max_tries - fails - 1
                tries_str = "tries"
                if attempts_left == 1:
                    tries_str = "try"
                # Add a punctuation mark if there isn't one
                if message[-1] not in "!().;?[]{}":
                    message = message + "."
                return {
                    "success": True,
                    "data": {
                        "status": "incorrect",
                        "message": "{} You have {} {} remaining.".format(
                            message, attempts_left, tries_str
                        ),
                    },
                }
            else:
                return {
                    "success": True,
                    "data": {"status": "incorrect", "message": message},
                }

    # Challenge already solved
    else:
        log(
            "submissions",
            "[{date}] {name} submitted {submission} on {challenge_id} with kpm {kpm} [ALREADY SOLVED]",
            name=user.name,
            submission=request_data.get("submission", "").encode("utf-8"),
            challenge_id=challenge_id,
            kpm=kpm,
        )
        return {
            "success": True,
            "data": {
                "status": "already_solved",
                "message": "You already solved this",
            },
        }


def load(app: Flask):
    app.view_functions['api.challenges_challenge_attempt'] = attempt_hooked
