-- Run this in your Supabase SQL Editor to add the missing columns
-- Dashboard → SQL Editor → New query → paste this → Run

ALTER TABLE web_verification
  ADD COLUMN IF NOT EXISTS university_location         text,
  ADD COLUMN IF NOT EXISTS university_is_medical_faculty boolean,
  ADD COLUMN IF NOT EXISTS university_4th_year_subjects  jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS university_known_professors   jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS hospital_location            text,
  ADD COLUMN IF NOT EXISTS hospital_has_specialty       boolean,
  ADD COLUMN IF NOT EXISTS scraper_flags                jsonb DEFAULT '[]'::jsonb;
