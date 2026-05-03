-- Doctor Verification System - Supabase Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Doctors Table (Main State Machine)
CREATE TABLE public.doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Doctor Info
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    specialty TEXT NOT NULL,
    declared_univ TEXT NOT NULL,
    
    -- Documents (Paths in Supabase Storage)
    document_paths TEXT[] DEFAULT '{}',
    
    -- Pipeline Status
    -- pending -> processing_a -> processing_b -> scraping -> ingesting -> ready_for_interview -> interview_done -> verdict_ready
    status TEXT DEFAULT 'pending',
    
    -- Interview Token (Sent via email)
    interview_token UUID DEFAULT uuid_generate_v4(),
    interview_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '72 hours'),
    
    -- Final Results
    verdict TEXT, -- 'VERIFIED', 'NEEDS_MANUAL_REVIEW', 'REJECTED'
    final_score FLOAT,
    report_json JSONB
);

-- Documents Analysis Table
CREATE TABLE public.documents_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID REFERENCES public.doctors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Pipeline A & B Results
    ocr_text TEXT,
    structured_profile JSONB,
    document_flags TEXT[] DEFAULT '{}',
    anomalies TEXT[] DEFAULT '{}',
    ocr_confidence FLOAT
);

-- Web Verification Table
CREATE TABLE public.web_verification (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID REFERENCES public.doctors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    university_confirmed BOOLEAN,
    hospital_confirmed BOOLEAN,
    dean_verified TEXT, -- 'true', 'false', 'unknown'
    web_sources TEXT[] DEFAULT '{}'
);

-- Interviews Table
CREATE TABLE public.interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID REFERENCES public.doctors(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    survey_qa JSONB,
    transcript_json JSONB,
    expression_log JSONB
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to doctors table
CREATE TRIGGER update_doctors_updated_at
    BEFORE UPDATE ON public.doctors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Setup RLS (Row Level Security) - Simplified for Hackathon
ALTER TABLE public.doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.web_verification ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;

-- Create policy allowing anyone to INSERT a new doctor (public submission)
CREATE POLICY "Allow public submissions" 
ON public.doctors FOR INSERT 
TO public 
WITH CHECK (true);

-- Create policy allowing anyone with an interview token to view their doctor record
CREATE POLICY "Allow reading own record by ID" 
ON public.doctors FOR SELECT 
TO public 
USING (true); -- In a real app, you would restrict this, but for hackathon UI it's easier

-- Service Role has bypass RLS automatically, so the Python backend will have full access.
