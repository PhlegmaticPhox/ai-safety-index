# Security policy

This repository builds **[aisafetytracker.org](https://aisafetytracker.org)**, and that domain is
the only thing in scope.

`aisafetyindex.org` is **not** this site. It is an unrelated third party's project that shares no
code, no data and no infrastructure with this one. The similarity to this repository's name is a
historical accident and has already caused one reviewer to test the wrong deployment.

## Reporting a vulnerability

Email **security@aisafetytracker.org**.

Include what you found, how to reproduce it, and what you think the impact is. A proof of concept
helps; a working exploit is not required and is not expected.

This repository is private, so GitHub's private vulnerability reporting is not available here and
there is no public issue tracker to use instead. Email is the whole channel.

Expect an acknowledgement within about a week. This is a personal project maintained by one
person, not a staffed programme, and saying so is more useful than promising a response time that
will not be met. There is no bounty.

## What is a security report, and what is a correction

They go to different addresses because they need different handling.

**A security report** is something that could let a third party do what they should not: run
script in the site's origin, alter what a reader is served, reach the build or deploy pipeline,
or obtain something private. Send those to **security@aisafetytracker.org** and please give us a
chance to fix it before writing about it publicly.

**A correction** is a wrong number, a dead or wrong citation, a licence stated incorrectly, or a
coding judgement you disagree with. Those go to **corrections@aisafetytracker.org**, and material
ones are listed on [/corrections/](https://aisafetytracker.org/corrections/).

If you are not sure which one you have, send it to the security address. Moving a report into the
open later is easy; the reverse is not.

## Scope

**In scope**

- `https://aisafetytracker.org` and anything it serves
- This repository: the site source, the ETL pipeline in `etl/`, and the GitHub Actions workflow
- The data pipeline's handling of external sources, which is where the untrusted input is

**Out of scope**

- `aisafetyindex.org`, which is somebody else's site
- Cloudflare's own infrastructure - report that to Cloudflare
- Cloudflare Web Analytics, the one third-party script the site loads - also Cloudflare's
- The third-party publishers this site cites and links to - report that to them
- Findings that depend on already having write access to this repository
- Denial of service, automated scanning, and anything requiring high request volume

## What the site is, which shapes what is plausible

Worth knowing before you spend time on it. The site is fully static: prerendered HTML served by
Cloudflare Workers static assets. There is **no database, no accounts, no cookies, no forms, no
API, and no server-side code that runs on a visitor request**. The site's own build ships no
JavaScript; the only script on any page is Cloudflare's analytics beacon, injected at the edge,
and the Content-Security-Policy permits that one origin and nothing else.

So SQL injection, authentication bypass, session attacks and CSRF have nothing here to act on.

The interesting surface is elsewhere, and it is genuinely interesting: the site ingests eight
external feeds and several external datasets every day, unattended, and renders them. If you can
get something through one of those, that is the finding worth having.

## Safe harbour

Good-faith research on the scope above is welcome. Please do not run high-volume scans, do not
attempt denial of service, do not access or modify data that is not yours, and do not attack the
third-party publishers this site cites - they provide their data for free and are not party to
this.
