<div align="center">

# Leon Holetz
Dr.Lnx

### Developer at N3XT Agency

Discord systems · Automation · Internal tooling<br>
I build private platforms for communities, and the pipelines that keep them running.

<br>

[![Website](https://img.shields.io/badge/Website-n3xt--agency.com-1D9470?style=for-the-badge&logoColor=white)](https://n3xt-agency.com)
[![Contact](https://img.shields.io/badge/Contact-contact@n3xt--agency.com-1D9470?style=for-the-badge&logoColor=white)](mailto:contact@n3xt-agency.com)

<br>

[![TypeScript](https://img.shields.io/badge/typescript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![discord.js](https://img.shields.io/badge/discord.js-14-5865F2?logo=discord&logoColor=white)](https://discord.js.org/)
[![Node](https://img.shields.io/badge/node-20.11+-5FA04E?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/sqlite-better--sqlite3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Actions](https://img.shields.io/badge/ci-github%20actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)

<br>

**[Overview](#overview)** ·
**[Work](#work)** ·
**[Stack](#stack)** ·
**[How I build](#how-i-build)** ·
**[Contact](#contact)**

</div>

<br>

---

## Overview

I work on systems that a community actually runs on — support, moderation, recruitment,
engagement — rather than one-off scripts bolted onto someone else's bot. The through-line
is consolidation: one codebase and one set of data instead of five third-party services
that each know a fifth of the story.

The same instinct shows up in the small stuff. If a job runs twice, it should run on a
cron; if a decision is a setting, it should not be a rebuild.

<table>
<tr><td><b>Building</b></td><td>N3XT.sys — a complete Discord server operating system</td></tr>
<tr><td><b>Focus</b></td><td>Bot platforms, automation, developer tooling</td></tr>
<tr><td><b>Approach</b></td><td>One system per client, deployed and managed end to end</td></tr>
<tr><td><b>Agency</b></td><td><a href="https://n3xt-agency.com">N3XT Agency</a></td></tr>
</table>

<br>

---

## Work

### [N3XT.sys](https://github.com/n3xtpy/N3XT.sys) — Discord server operating system

*One bot, one dedicated instance per community, replacing the usual stack of five or six.*

Support tickets, moderation, staff recruitment, engagement, temporary voice, surveys,
anti-raid, ban appeals, audit logs and presentation — all on one codebase and one dataset,
so a member's ticket history, moderation record, staff status and activity level can appear
in the same place.

| | |
| --- | --- |
| **Stack** | TypeScript · discord.js 14 · Node 20 · better-sqlite3 |
| **Interface** | Native Discord panels, plus an Ink/React operator console in the terminal |
| **Quality** | Typecheck, lint and tests on every push |
| **Deployment** | Dedicated instance per server, hard-locked to that guild |

<br>

---

## Stack

| Area | What I reach for |
| :-- | :-- |
| **Languages** | TypeScript · Python · JavaScript |
| **Runtime** | Node 20 · discord.js · React (Ink) |
| **Data** | SQLite / better-sqlite3 |
| **Automation** | GitHub Actions · cron · shell |
| **Quality** | ESLint · Vitest · `tsc --noEmit` |

<br>

---

## How I build

<table>
<tr>
<td width="50%" valign="top">

#### Configuration over hardcoding

Channels, roles, thresholds, timers and wording are settings. Changing how many warnings
trigger a ban, or where tickets open, is a config change — not a release.

</td>
<td width="50%" valign="top">

#### Built to survive restarts

Timed actions, scheduled jobs and in-progress state are restored from storage. A reboot
mid-task is an inconvenience, not data loss.

</td>
</tr>
<tr>
<td width="50%" valign="top">

#### Failure is a no-op

When an upstream is rate-limited or unreachable, jobs log a skip and exit clean. A bad
network day leaves yesterday's good state in place instead of writing a broken one.

</td>
<td width="50%" valign="top">

#### Checked before it ships

Typecheck, lint and tests run on every push. The interesting bugs are the ones a compiler
cannot catch, so the boring ones should never reach a review.

</td>
</tr>
</table>

<br>

---

## Contact

Work enquiries, custom systems, or a scoping call for a deployment — either channel reaches
me directly.

<div align="center">
<br>

[![Get in touch](https://img.shields.io/badge/Get_in_touch-contact@n3xt--agency.com-1D9470?style=for-the-badge&logoColor=white)](mailto:contact@n3xt-agency.com)
[![Visit website](https://img.shields.io/badge/Visit-n3xt--agency.com-24292F?style=for-the-badge&logoColor=white)](https://n3xt-agency.com)

</div>

<br>

---

<div align="center">

**N3XT Agency**<br>
[n3xt-agency.com](https://n3xt-agency.com) · [contact@n3xt-agency.com](mailto:contact@n3xt-agency.com)

</div>
