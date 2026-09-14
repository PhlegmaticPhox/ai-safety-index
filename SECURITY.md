# Security policy

This repository builds **[aisafetytracker.org](https://aisafetytracker.org)**, and that domain is
the only thing in scope.

`aisafetyindex.org` is **not** this site. It is an unrelated third party's project that shares no
code, no data and no infrastructure with this one. The similarity to this repository's name is a
historical accident and has already caused one reviewer to test the wrong deployment.

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting**, not a public issue:

1. Open the [Security tab](https://github.com/PhlegmaticPhox/ai-safety-index/security) of this
   repository.
2. Choose **Report a vulnerability**.
3. Describe what you found, how to reproduce it, and what you think the impact is.

That channel is private between you and the maintainer until a fix is published. There is no
security contact address here on purpose: this project publishes no email address anywhere, and
GitHub's own reporting flow does the job without one.

Expect an acknowledgement within about a week. This is a personal project maintained by one
person, not a staffed programme, and saying so is more useful than promising a response time that
will not be met.

## What is a security report, and what is a correction

These go to different places, and the distinction matters because one of them is public by design.

**A security report** is something that could let a third party do what they should not: run
script in the site's origin, alter what a reader is served, reach the build or deploy pipeline,
or obtain something private. Report those privately, as above.

**A correction** is a wrong number, a dead or wrong citation, a licence stated incorrectly, or a
coding judgement you disagree with. Those go in a **[public
issue](https://github.com/PhlegmaticPhox/ai-safety-index/issues/new)**, and they are public
deliberately - see [/corrections/](https://aisafetytracker.org/corrections/). A site whose whole
argument is that you can check where a number came from cannot then fix its mistakes quietly.

If you are not sure which one you have, report it privately. Moving a report into the open later
is easy; the reverse is not.

## Scope

**In scope**

- `https://aisafetytracker.org` and anything it serves
- This repository: the site source, the ETL pipeline in `etl/`, and the GitHub Actions workflow
- The data pipeline's handling of external sources, which is where the untrusted input is

**Out of scope**

- `aisafetyindex.org`, which is somebody else's site
- Cloudflare's own infrastructure - report that to Cloudflare
- The third-party publishers this site cites and links to - report that to them
- Findings that depend on already having write access to this repository
- Denial of service, automated scanning, and anything requiring high request volume

## What the site is, which shapes what is plausible

Worth knowing before you spend time on it. The site is fully static: 32 prerendered HTML pages
served by Cloudflare Workers static assets. There is **no database, no accounts, no cookies, no
forms, no API, no server-side code that runs on a visitor request, and no client-side JavaScript
at all**. So SQL injection, authentication bypass, session attacks and CSRF have nothing to act
on.

The interesting surface is elsewhere, and it is genuinely interesting: the site ingests eight
external feeds and several external datasets every day, unattended, and renders them. If you can
get something through one of those, that is the finding worth having.

## Safe harbour

Good-faith research on the scope above is welcome. Please do not run high-volume scans, do not
attempt denial of service, do not access or modify data that is not yours, and do not attack the
third-party publishers this site cites - they provide their data for free and are not party to
this.
