# SPE Board Guide

## Project
- **Key:** SPE (sc0red Platform Engineering)
- **Type:** Team-managed (next-gen), Jira Software
- **Instance:** sc0red.atlassian.net
- **Board:** <https://sc0red.atlassian.net/jira/software/projects/SPE/board>

## Workflow Statuses

Statuses flow roughly left-to-right. All statuses allow "Any" transitions (you can move between any two statuses), but the intended flow is described below.

### Intake
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **New** | 10000 | To Do | Freshly created. Hasn't been looked at yet. |
| **Backlog** | 10020 | To Do | Acknowledged but not prioritized for current work. |
| **Triage** | 10003 | To Do | Being evaluated — needs investigation, reproduction, or scoping before it can be worked. |

### Planning (AI-Assisted)
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **Plan** | 10072 | To Do | Assigned to Patch for analysis. She reads the code, develops a plan of attack, estimates Risk/Intensity/Story Points, and posts findings as a Jira comment. Patch transitions to Plan Review when done. |
| **Plan Review** | 10073 | To Do | Patch posted her plan. Chris reviews the analysis, estimates, and proposed approach. If approved, Chris moves to Ready for Development. If the plan needs work, Chris moves back to Plan or Triage. |

### Development
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **Ready for Development** | 10004 | To Do | **Approved for implementation.** The plan has been reviewed and Chris has greenlit the work. Patch picks this up (one at a time, highest priority first), transitions to In Development, and starts coding. |
| **In Development** | 10001 | In Progress | Actively being worked. A branch exists and code is being written. |
| **Dev Blocked** | 10005 | To Do | Work is blocked — waiting on another team, missing access, dependency issue, or architectural question that needs a decision. |

### Verification
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **Deployed to Dev** | 10019 | In Progress | PR merged to `development` branch and deployed to dev environment. Ready for verification. |
| **Verify in Test** | 10021 | In Progress | Deployed to `testing` environment. Being verified against acceptance criteria. |
| **Verify Blocked** | 10043 | In Progress | Verification is blocked — environment issue, missing test data, or dependency on another ticket. |

### Release
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **Ready for Production** | 10018 | In Progress | Verified in testing. Waiting for the next production deploy window. |
| **Deployed to Production** | 10002 | Done | Live in production. Ticket complete. |

### Terminal
| Status | ID | Category | Purpose |
|--------|----|----------|---------|
| **Abandon** | 10022 | Done | Won't fix, duplicate, or no longer relevant. |

## Intended Flow

```
New → Triage → Plan → Plan Review → Ready for Development → In Development → Deployed to Dev → Verify in Test → Ready for Production → Deployed to Production
```

Shortcuts and branches:
- **New → Backlog** — acknowledged but deprioritized
- **Triage → Abandon** — not worth fixing
- **Any → Dev Blocked / Verify Blocked** — work is stuck, needs intervention
- **Plan Review → Triage** — plan rejected, needs rethinking
- **Plan Review → Plan** — plan needs more analysis

## Transition IDs

| Transition | ID | Who |
|------------|----|-----|
| → New | 11 | Anyone |
| → Triage | 16 | Anyone |
| → Plan | 12 | Chris (moves ticket here for Patch to analyze) |
| → Plan Review | 13 | Patch (autonomous — after posting plan) |
| → Ready for Development | 3 | Chris (approves the plan) |
| → In Development | 21 | Patch (starts implementation) |
| → Dev Blocked | 4 | Anyone |
| → Deployed to Dev | 8 | Patch (after PR merge) |
| → Verify in Test | 10 | Anyone |
| → Verify Blocked | 5 | Anyone |
| → Ready for Production | 7 | Anyone |
| → Deployed to Production | 31 | Chris (production deploy gate is human) |
| → Backlog | 2 | Anyone |
| → Abandon | 9 | Anyone |

## Rules
- **Nothing over 5 story points goes to In Development** without being broken down first.
- **One ticket In Development at a time** for Patch. Serial queue, highest priority first.
- **Production deploys are human-gated.** Patch does not deploy to production.
- **Risk is set by the person doing the work.** What's low risk for a senior engineer might be high risk for AI (and vice versa).

## Issue Types
All issue types share the same workflow: Task, Bug, Story, Epic, Subtask, Manual Test, Automated Test, Unit Test.
