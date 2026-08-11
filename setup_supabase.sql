-- SmartSMBAI HR Recruitment Suite — Supabase Setup
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS candidates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    region TEXT NOT NULL CHECK (region IN ('Europe','Africa','Latin America','Canada','USA','Unknown')),
    source TEXT DEFAULT 'email',
    status TEXT DEFAULT 'new' CHECK (
        status IN ('new','screening','interview_sent','interview_complete',
                   'scoring','shortlisted','rejected','offered','certified'))
);

CREATE TABLE IF NOT EXISTS applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    email_subject TEXT,
    email_body TEXT,
    cv_text TEXT,
    cover_letter_text TEXT,
    raw_email_uid TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS cv_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    sales_track_record INTEGER CHECK (sales_track_record BETWEEN 1 AND 5),
    local_network_proof INTEGER CHECK (local_network_proof BETWEEN 1 AND 5),
    tech_ai_prompting_readiness INTEGER CHECK (tech_ai_prompting_readiness BETWEEN 1 AND 5),
    ai_troubleshooting_integration_privacy INTEGER CHECK (ai_troubleshooting_integration_privacy BETWEEN 1 AND 5),
    ai_adoption_metrics_thinking INTEGER CHECK (ai_adoption_metrics_thinking BETWEEN 1 AND 5),
    communication_clarity INTEGER CHECK (communication_clarity BETWEEN 1 AND 5),
    region_fit INTEGER CHECK (region_fit BETWEEN 1 AND 5),
    total_score INTEGER,
    recommendation TEXT CHECK (recommendation IN ('Advance','Hold','Reject')),
    summary TEXT,
    green_flags JSONB DEFAULT '[]',
    red_flags JSONB DEFAULT '[]',
    model_used TEXT DEFAULT 'claude-sonnet-4-6'
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    invite_sent_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,
    region TEXT,
    questions JSONB DEFAULT '[]',
    responses JSONB DEFAULT '[]',
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending','sent','in_progress','completed','expired'))
);

CREATE TABLE IF NOT EXISTS interview_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    scored_at TIMESTAMPTZ DEFAULT NOW(),
    sales_track_record INTEGER,
    local_network_proof INTEGER,
    tech_ai_prompting_readiness INTEGER,
    ai_troubleshooting_integration_privacy INTEGER,
    ai_adoption_metrics_thinking INTEGER,
    communication_clarity INTEGER,
    region_fit INTEGER,
    total_score INTEGER,
    recommendation TEXT CHECK (recommendation IN ('Advance','Hold for Human Review','Do Not Advance')),
    summary TEXT,
    evidence_highlights JSONB DEFAULT '[]',
    risks_or_concerns JSONB DEFAULT '[]',
    recommended_follow_up_questions JSONB DEFAULT '[]',
    compliance_and_fairness_notes TEXT,
    model_used TEXT DEFAULT 'claude-sonnet-4-6'
);

CREATE TABLE IF NOT EXISTS human_reviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMPTZ DEFAULT NOW(),
    reviewer_name TEXT NOT NULL,
    stage TEXT NOT NULL,
    decision TEXT CHECK (decision IN ('advance','hold','reject','offer','certify')),
    notes TEXT,
    override_reason TEXT
);

CREATE TABLE IF NOT EXISTS hr_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    action TEXT NOT NULL,
    actor TEXT DEFAULT 'system',
    object_type TEXT,
    object_id UUID,
    summary TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_candidates_status  ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_region  ON candidates(region);
CREATE INDEX IF NOT EXISTS idx_candidates_email   ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_applications_cand  ON applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_cv_scores_app      ON cv_scores(application_id);
CREATE INDEX IF NOT EXISTS idx_sessions_cand      ON interview_sessions(candidate_id);
CREATE INDEX IF NOT EXISTS idx_audit_time         ON hr_audit_log(timestamp_utc DESC);

SELECT 'SmartSMBAI HR Suite tables created.' AS result;
