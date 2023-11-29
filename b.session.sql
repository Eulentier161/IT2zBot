SELECT p.question, COUNT(po.option_id) count, po.value, po.symbol FROM poll p
JOIN poll_option po ON p.poll_id = po.poll_id
JOIN poll_option_vote pov ON po.option_id = pov.option_id
WHERE p.poll_id = 1
GROUP BY po.option_id, po.value, po.symbol
;