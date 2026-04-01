USE food_inspections;

DROP PROCEDURE IF EXISTS food_inspections.get_all_restaurants_search_options;
DROP PROCEDURE IF EXISTS food_inspections.get_avg_rating;
DROP PROCEDURE IF EXISTS food_inspections.get_avg_violations_per_inspection;
DROP PROCEDURE IF EXISTS food_inspections.get_inspection_count;
DROP PROCEDURE IF EXISTS food_inspections.get_restaurant_count;
DROP PROCEDURE IF EXISTS food_inspections.get_restaurant_violations;
DROP PROCEDURE IF EXISTS food_inspections.get_restaurant_violations_count;
DROP PROCEDURE IF EXISTS food_inspections.get_review_count;
DROP PROCEDURE IF EXISTS food_inspections.get_violations_by_level;
DROP PROCEDURE IF EXISTS food_inspections.get_violations_per_year;
DROP PROCEDURE IF EXISTS food_inspections.search_by_name_restaurant;

DROP PROCEDURE IF EXISTS get_restaurant_count;
DELIMITER //
CREATE PROCEDURE get_restaurant_count()
BEGIN
    SELECT COUNT(*) FROM restaurant;
END//
DELIMITER ;


DROP PROCEDURE IF EXISTS get_inspection_count;
DELIMITER //
CREATE PROCEDURE get_inspection_count()
BEGIN
    SELECT COUNT(*) FROM inspection;
END//
DELIMITER ;

DROP PROCEDURE IF EXISTS get_review_count;
DELIMITER //
CREATE PROCEDURE get_review_count()
BEGIN
    SELECT SUM(review_count) FROM restaurant;
END//
DELIMITER ;

DROP PROCEDURE IF EXISTS get_avg_rating;
DELIMITER //
CREATE PROCEDURE get_avg_rating()
BEGIN
    SELECT ROUND(AVG(avg_rating), 2) FROM restaurant;
END//
DELMITER ;

DROP PROCEDURE IF EXISTS get_avg_violations_per_inspection;
DELIMITER //
CREATE PROCEDURE get_avg_violations_per_inspection()
BEGIN
    SELECT ROUND(AVG(violation_count), 2)
    FROM (
        SELECT COUNT(*) as violation_count
        FROM violation_log
        GROUP BY license_num, result_datetime
    ) counts;
END//
DELIMITER ;

DROP PROCEDURE IF EXISTS get_violations_by_level;
DELIMITER //
CREATE PROCEDURE get_violations_by_level()
BEGIN
    SELECT violation_level, COUNT(*) as count
    FROM violation_key
    GROUP BY violation_level;
END//
DELMITER ;

DROP PROCEDURE IF EXISTS get_violations_per_year;
DELIMITER //
CREATE PROCEDURE get_violations_per_year()
BEGIN
    SELECT YEAR(status_date) as year, COUNT(*) as count
    FROM violation_log
    GROUP BY YEAR(status_date)
    ORDER BY year;
END//
DELIMITER ;

DROP PROCEDURE IF EXISTS get_all_restaurants_search_options;
DELIMITER $$
CREATE PROCEDURE get_all_restaurants_search_options()
BEGIN
	-- , street_num, city
	SELECT business_name, street_num, city FROM restaurant
		INNER JOIN address USING (property_id);
END $$
DELIMITER ;

CALL get_all_restaurants_search_options;

DROP PROCEDURE IF EXISTS search_by_name_restaurant;
DELIMITER $$
-- Returns the street and city for restaurants with names like the search
CREATE PROCEDURE search_by_name_restaurant(business_name_p varchar(512))
BEGIN


	SELECT street_num, city FROM restaurant 
		INNER JOIN address USING (property_id)
        WHERE business_name LIKE (business_name_p);
END $$
DELIMITER ;

CALL search_by_name_restaurant('Dunkin'); -- 3
CALL get_all_restaurants_search_options;
CALL search_by_name_restaurant('Williams'); -- 0
SELECT street_num, city FROM restaurant 
	INNER JOIN address USING (property_id)
	WHERE business_name LIKE ('Bell');

DROP PROCEDURE IF EXISTS get_restaurant_violations;
DELIMITER $$
CREATE PROCEDURE get_restaurant_violations(license_num_p INT)
BEGIN
	SELECT * FROM violation_log WHERE license_num = license_num_p;
END $$
DELIMITER ;

SELECT * FROM restaurant WHERE business_name LIKE ('Dunkin');
CALL get_restaurant_violations(18174); -- 41 rows

DROP PROCEDURE IF EXISTS get_restaurant_violations_count;
DELIMITER $$
CREATE PROCEDURE get_restaurant_violations_count(IN license_num_p INT, OUT vio_count INT)
BEGIN
	SELECT COUNT(*) INTO vio_count FROM violation_log WHERE license_num = license_num_p;
END $$
DELIMITER ;

SET @vc = 0;
CALL get_restaurant_violations_count(18174, @vc);
SELECT @vc; -- 41 ( matches CALL get_restaurant_violations(18174) rows )

SELECT violation_level, COUNT(*) as count
FROM violation_key
GROUP BY violation_level
ORDER BY count DESC;

SELECT * FROM restaurant;