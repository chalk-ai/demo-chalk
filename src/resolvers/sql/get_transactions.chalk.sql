-- source: postgres
-- resolves: Transaction
-- type: online

SELECT
    id,
    amount,
    at,
    at AS created_at,
    category,
    direction,
    merchant,
    status,
    user_id
FROM transactions
