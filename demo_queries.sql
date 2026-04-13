USE food_inspections;


-- all dashboard elements are populated with SQL queries
CALL get_violations_by_level;

SELECT * FROM restaurant
WHERE business_name = "Savin Scoops";


-- main user CRUD operations performed on restaurant reviews
SELECT * FROM app_user
	JOIN review USING(username) 
WHERE username = "helen.me";

