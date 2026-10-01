-- source: postgres
-- resolves: CreditReport
-- type: online

SELECT
    id,
    num_tradelines,
    percent_past_due,
    score,
    total_balance,
    user_id
FROM credit_reports
