# Project Instructions

This project identifies Swiss freelance and B2B opportunities for
Aber Industrial Solutions and its employees.

## Product Goal

The system continuously collects relevant opportunities, evaluates them
against employee and company profiles, and produces a concise weekly report
for human review.

The weekly report should eventually contain:

* top individual freelance matches
* top company/project opportunities
* new tenders
* opportunities closing soon
* match scores and reasons
* relevant employees for each opportunity
* major skill or availability gaps
* links to the original postings

The report is the primary review interface.
A web dashboard is optional and should not be assumed to be necessary.

## Context

Temporary background material is available under `context/`. It currently contains a company-wide work summary, individual work summaries for Salomon Aengenheyster-Aber, Mark Aber, and Günter Bernhart, and the company's ISO management system under `context/managment-system/`. Use this material to understand the company, employee capabilities, delivered projects, responsibilities, and operating context. The `context/` directory is for design and research only; application code should not depend on it, and important conclusions should eventually be distilled into durable documentation or structured profiles.

## Current Milestone

Build a deterministic opportunity-normalization and matching pipeline.

Do NOT yet build:

* web scraping
* scheduled weekly report delivery
* automatic job applications
* a web dashboard
* autonomous outreach

unless explicitly requested.

## Target Pipeline

raw opportunity
→ normalization
→ deduplication
→ hard filters
→ semantic matching
→ scoring
→ opportunity database
→ weekly report
→ human review

## Engineering Rules

* Python 3.13+
* Pydantic for domain schemas
* pytest for tests
* type hints everywhere
* pure functions where practical
* external services behind interfaces
* LLM output must use structured schemas
* deterministic filtering happens before LLM scoring
* never infer candidate skills without evidence
* retain original posting text and source URL
* every rejection must have a reason code
* preserve enough structured data to generate reports without reprocessing
  the original posting
* human approval is required before any application or outreach
