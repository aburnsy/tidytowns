---
title: "Our public project tracker and village map"
delivery_year: 2026
completed_year: 2026
tags:
  - community
status: "Live and growing"
cost_estimate: "€0 (built and hosted in-kind)"
benefit: "High"
volunteer_hours: "Months of evenings and weekends to build, plus weekly updates as the work progresses"
inspired_by: "The adjudicator's recommendation that committees publish a formal 3/5-year plan"
---

The site you're reading right now is the public tracker for everything TMB Tidy Towns is doing, and we built it ourselves from scratch. It is also our formal multi-year plan, in line with the adjudicator's repeated recommendation that committees publish a 3/5-year vision. The committee took the view that a static PDF nobody opens isn't really a plan, so we built this instead, a living, openly auditable, project-by-project record that anyone can read at any time.

## What's actually on it

There are 28 projects on the site at the time of writing, split across active, completed and future. Every one has a status, an indicative cost, a benefit level, a delivery year, and a write-up of what's involved. Most have photographs. The completed ones include what they actually came in at and the photos to back the work up.

Sitting alongside the project list is the [Village Map](../../map.md), an interactive map with 30 marked locations and 72 photographs pinned to specific spots in the village. Click on any pin and you can see what's there, what's happening, and the photos to go with it. It's the easiest way for an adjudicator (or anyone visiting) to navigate what we're working on and where.

## Why this is our 3/5-year plan

The site does exactly what a formal multi-year plan is supposed to do. It's structured, it covers multiple years, and it links specific projects back to specific adjudicator recommendations. Where a static PDF version of a five-year plan starts going out of date the day it's signed off, this one is updated as the work is done. By the time the next adjudicator comes through, the version they read will be the current version, not last year's.

It's also useful to us as a committee, not just to the adjudicator. We can see at a glance what's planned for this year, what's still on the future pile, and what's already in the ground.

## What it took to build

A substantial body of volunteer work over months of evenings and weekends. The site was built from scratch using mkdocs material, with a small custom python layer doing the heavy lifting so that every project's status, cost, benefit and tags render automatically from a single piece of frontmatter. The map sits on top of openstreetmap with our own marker data and photo galleries. The whole thing is hosted on github pages, so the running cost is zero and stays zero.

## What's next

The site keeps growing. As projects land, we add the photographs, update the costs to actuals, and shift them across to *Completed*. As new ideas come in from the committee, residents or the adjudicator, they go onto *Future*. The plan never goes stale, because the plan is the work.
