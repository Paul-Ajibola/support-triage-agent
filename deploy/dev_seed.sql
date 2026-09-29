-- DEV ONLY. Fake data for local testing. Never run in production.

INSERT INTO accounts (account_id, tier, monthly_spend, rate_limit)
VALUES ('ACC-001', 'enterprise', 4200.00, 10000)
ON CONFLICT (account_id) DO NOTHING;

INSERT INTO tickets (ticket_id, title, body, resolution, category)
VALUES ('T-1001', 'Login fails after password reset', 'User reset password but still gets 401 on login.', 'Cleared cached session tokens; user re-logged in successfully.', 'auth')
ON CONFLICT (ticket_id) DO NOTHING;

INSERT INTO tickets (ticket_id, title, body, resolution, category)
VALUES ('T-1002', 'API rate limit hit unexpectedly', 'Customer says they hit rate limit despite low usage.', 'Found a misconfigured burst limit on their tier; adjusted config.', 'billing')
ON CONFLICT (ticket_id) DO NOTHING;

INSERT INTO tickets (ticket_id, title, body, resolution, category)
VALUES ('T-1003', 'Webhook not firing', 'Webhook events stopped arriving after endpoint URL change.', 'Endpoint URL had trailing slash mismatch; corrected URL.', 'integration')
ON CONFLICT (ticket_id) DO NOTHING;
