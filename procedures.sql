USE food_inspections;

DROP PROCEDURE IF EXISTS get_restaurant_count;
DELIMITER $$
CREATE PROCEDURE get_restaurant_count()
BEGIN
    SELECT COUNT(*) FROM restaurant;
END$$
DELIMITER ;


DROP PROCEDURE IF EXISTS get_inspection_count;
DELIMITER $$
CREATE PROCEDURE get_inspection_count()
BEGIN
    SELECT COUNT(*) FROM inspection;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_review_count;
DELIMITER $$
CREATE PROCEDURE get_review_count()
BEGIN
    SELECT SUM(review_count) FROM restaurant;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_avg_rating;
DELIMITER $$
CREATE PROCEDURE get_avg_rating()
BEGIN
    SELECT ROUND(AVG(avg_rating), 2) FROM restaurant;
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS get_avg_violations_per_inspection;
DELIMITER $$
CREATE PROCEDURE get_avg_violations_per_inspection()
BEGIN
    SELECT ROUND(AVG(violation_count), 2)
    FROM (
        SELECT COUNT(*) as violation_count
        FROM violation_log
        GROUP BY license_num, result_datetime
    ) counts;
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS get_violations_by_level;
DELIMITER $$
CREATE PROCEDURE get_violations_by_level()
BEGIN
    SELECT violation_level, COUNT(*) as count
    FROM violation_key
    GROUP BY violation_level;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_violations_per_year;
DELIMITER $$
CREATE PROCEDURE get_violations_per_year()
BEGIN
    SELECT YEAR(status_date) as year, COUNT(*) as count
    FROM violation_log
    GROUP BY YEAR(status_date)
    ORDER BY year;
END$$
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

DROP PROCEDURE IF EXISTS get_restaurant_violations;
DELIMITER $$
CREATE PROCEDURE get_restaurant_violations(license_num_p INT)
BEGIN
	SELECT * FROM violation_log WHERE license_num = license_num_p;
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_restaurant_violations_count;
DELIMITER $$
CREATE PROCEDURE get_restaurant_violations_count(IN license_num_p INT, OUT vio_count INT)
BEGIN
	SELECT COUNT(*) INTO vio_count FROM violation_log WHERE license_num = license_num_p;
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS insert_user_if_not_exists;
DELIMITER $$
CREATE PROCEDURE insert_user_if_not_exists(
    IN p_username VARCHAR(32),
    IN p_city VARCHAR(32),
    IN p_state CHAR(2)
)
BEGIN
    INSERT IGNORE INTO app_user (username, home_city, home_state)
    VALUES (p_username, p_city, p_state);
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS insert_review;
DELIMITER $$
CREATE PROCEDURE insert_review(
    IN p_license_num INT,
    IN p_username VARCHAR(32),
    IN p_comment TEXT,
    IN p_rating ENUM('0','1','2','3','4','5')
)
BEGIN
    INSERT INTO review (license_num, username, review_comment, rating, review_date)
    VALUES (p_license_num, p_username, p_comment, p_rating, CURDATE());
END$$

DELIMITER ;

DROP TRIGGER IF EXISTS after_review_insert;
DELIMITER $$
CREATE TRIGGER after_review_insert
AFTER INSERT ON review
FOR EACH ROW
BEGIN
    UPDATE restaurant
    SET review_count = review_count + 1,
        avg_rating = (
            SELECT AVG(CAST(rating AS DECIMAL))
            FROM review
            WHERE license_num = NEW.license_num
        )
    WHERE license_num = NEW.license_num;
END$$



-- sandbox
SELECT * FROM restaurant WHERE business_name LIKE ('Dunkin');
CALL get_restaurant_violations(18174); -- 41 rows

CALL search_by_name_restaurant('Dunkin'); -- 3
CALL get_all_restaurants_search_options;
CALL search_by_name_restaurant('Williams'); -- 0
SELECT street_num, city FROM restaurant 
	INNER JOIN address USING (property_id)
	WHERE business_name LIKE ('Bell');

SET @vc = 0;
CALL get_restaurant_violations_count(18174, @vc);
SELECT @vc; -- 41 ( matches CALL get_restaurant_violations(18174) rows )

SELECT violation_level, COUNT(*) as count
FROM violation_key
GROUP BY violation_level
ORDER BY count DESC;

SELECT * FROM restaurant;