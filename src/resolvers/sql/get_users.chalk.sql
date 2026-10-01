-- source: postgres
-- resolves: User
-- type: online

SELECT
    id,
    created_at,
    denylisted,
    email,
    email_age_days,
    is_fraud,
    name,
    name_email_match_score,
    risk_score
FROM users
