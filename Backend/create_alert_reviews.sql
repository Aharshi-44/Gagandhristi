-- Migration: Create alert_reviews table for analyst review and human-in-the-loop verification
CREATE TABLE IF NOT EXISTS alert_reviews (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(100) NOT NULL,
    review_status VARCHAR(50) NOT NULL, -- 'CONFIRMED', 'FALSE_ALARM', 'REJECTED', 'INVESTIGATING'
    confidence_rating VARCHAR(20) DEFAULT 'HIGH', -- 'HIGH', 'MEDIUM', 'LOW'
    notes TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_reviews_alert_id ON alert_reviews(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_reviews_reviewed_at ON alert_reviews(reviewed_at DESC);
