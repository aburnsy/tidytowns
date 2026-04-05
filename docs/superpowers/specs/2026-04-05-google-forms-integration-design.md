# Google Forms Integration for TMB Tidy Towns

**Date:** 2026-04-05
**Status:** Design approved

## Problem

The current site requires committee members to run bash scripts and edit markdown files to contribute. Non-technical volunteers can't participate. Google Form placeholder pages exist but were never set up.

## Solution

Embed 3 Google Forms in the MkDocs site. Committee members submit via browser. Andre reviews the linked Google Sheet weekly and uses existing scripts to publish approved content.

## Workflow

1. Committee member visits site, fills in a Google Form
2. Submission lands in a Google Sheet (auto-linked to the form)
3. Andre reviews Sheet weekly
4. Andre runs `new-project.sh` / `new-task.sh` for approved items
5. Andre rebuilds and deploys

## Forms

### Form 1: Propose a Project

| Field | Type | Required |
|-------|------|----------|
| Your name | Short text | No |
| Project idea (title) | Short text | Yes |
| Description | Long text | Yes |
| Category | Dropdown: Community, Streetscape, Green Spaces, Nature & Biodiversity, Sustainability, Tidiness, Residential, Approach Roads | Yes |
| Why is it important? | Long text | No |
| Estimated cost | Short text | No |
| Location in village | Short text | No |

### Form 2: Comment on a Project

| Field | Type | Required |
|-------|------|----------|
| Your name | Short text | No |
| Which project? | Dropdown: (current project list) | Yes |
| Your comment or idea | Long text | Yes |
| Would you like to help? | Multiple choice: Yes / No / Maybe | No |

### Form 3: Volunteer for a Task

| Field | Type | Required |
|-------|------|----------|
| Your name | Short text | Yes |
| Which project? | Dropdown: (current project list) | Yes |
| What can you help with? | Long text | Yes |
| Availability | Dropdown: Weekday mornings, Weekday evenings, Weekends, Flexible | Yes |

## Site Changes

### Modified files

1. `site/docs/propose-project.md` - Replace placeholder with Form 1 iframe
2. `site/docs/submit-idea.md` - Replace placeholder with Form 2 iframe
3. `site/mkdocs.yml` - Add Volunteer to nav

### New files

4. `site/docs/volunteer.md` - New page with Form 3 iframe

### Bulk update

5. All `site/docs/projects/*/index.md` - Update footer links to point to actual form pages

## Implementation

1. Create 3 Google Forms via browser automation in user's Chrome
2. Get embed URLs from each form
3. Update site markdown files with iframe embeds
4. Update project page footers
5. Rebuild site

## Maintenance

- When new projects are added, update the project dropdown in Forms 2 and 3 (manual, ~1 min)
- No API keys, service accounts, or ongoing technical maintenance required
