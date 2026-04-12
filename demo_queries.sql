USE food_inspections;

CALL get_violations_by_level;

SELECT * FROM app_user
	JOIN review USING(username) 
WHERE username = "helen.me";

