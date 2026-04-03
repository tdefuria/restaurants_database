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
	SELECT restaurant.license_num, business_name, street_num, city FROM restaurant
		INNER JOIN address USING (property_id);
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS search_by_name_restaurant;
DELIMITER $$
-- Returns the street and city for restaurants with names like the search
CREATE PROCEDURE search_by_name_restaurant(business_name_p varchar(512))
BEGIN
	IF ((SELECT COUNT(license_num) FROM restaurant WHERE business_name LIKE (CONCAT('%', business_name_p, '%'))) = 0)
		THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "No restaurant found by that keyword in the violations database"; 
	END IF;
	SELECT latitude, longitude, 
		restaurant.license_num, business_name, street_num, city FROM restaurant 
			INNER JOIN address USING (property_id)
			WHERE business_name LIKE (CONCAT('%', business_name_p, '%'));
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_restaurant_violations;
DELIMITER $$
CREATE PROCEDURE get_restaurant_violations(license_num_p INT)
BEGIN
	-- UNLIKELY to happen, because we plan to use this only after retrieving the license_nums from the database
	IF ((SELECT COUNT(*) FROM restaurant WHERE license_num = license_num_p) = 0)
		THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "Restaurant not found by that keyword in the violations database";
	END IF;
	SELECT * FROM violation_log 
		INNER JOIN violation_key USING (type_code) WHERE license_num = license_num_p;
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
DELIMITER ;

DROP PROCEDURE IF EXISTS get_restaurant_locations;
DELIMITER $$
CREATE PROCEDURE get_restaurant_locations()
BEGIN
	SELECT latitude, longitude, business_name, 
		restaurant.license_num, street_num, city 
			FROM restaurant
			INNER JOIN address USING (license_num);
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS total_tract_violations;
DELIMITER $$
CREATE PROCEDURE total_tract_violations(IN tract_id_p CHAR(11), OUT tract_count_p INT)
BEGIN
	SELECT COUNT(*) INTO tract_count_p FROM violation_log
		INNER JOIN restaurant USING(license_num)
        INNER JOIN address USING (license_num)
        INNER JOIN land_parcel ON land_parcel.land_parcel_id = address.land_parcel_id
        INNER JOIN census_block USING (block_id)
        INNER JOIN census_block_group USING (block_group_id)
        INNER JOIN census_tract USING (tract_id)
        WHERE tract_id = tract_id_p;
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS total_tract_restaurants;
DELIMITER $$
CREATE PROCEDURE total_tract_restaurants(IN tract_id_p CHAR(11), OUT tract_count_p INT)
BEGIN
	SELECT COUNT(DISTINCT license_num) INTO tract_count_p FROM violation_log
		INNER JOIN restaurant USING(license_num)
        INNER JOIN address USING (license_num)
        INNER JOIN land_parcel ON land_parcel.land_parcel_id = address.land_parcel_id
        INNER JOIN census_block USING (block_id)
        INNER JOIN census_block_group USING (block_group_id)
        INNER JOIN census_tract USING (tract_id)
        WHERE tract_id = tract_id_p;
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_each_tract_violations_count;
DELIMITER $$
CREATE PROCEDURE get_each_tract_violations_count()
BEGIN
	DECLARE row_not_found INT;
	DECLARE current_tract_id CHAR(11);
    DECLARE current_tract_count INT;
    DECLARE census_tract_c CURSOR FOR
		SELECT tract_id FROM census_tract;
    DECLARE CONTINUE HANDLER FOR NOT FOUND
		SET row_not_found = TRUE;
	-- handle errors as needed
    SET row_not_found = FALSE;
    OPEN census_tract_c;
    WHILE row_not_found = FALSE DO
		FETCH census_tract_c INTO current_tract_id;
        SET current_tract_count = 0;
		CALL total_tract_violations(current_tract_id, current_tract_count);
        SELECT current_tract_id, current_tract_count;
	END WHILE;
END $$
DELIMITER ;

DROP PROCEDURE IF EXISTS get_reviews_by_user;
DELIMITER $$
CREATE PROCEDURE get_reviews_by_user(IN p_username VARCHAR(32))
BEGIN
    SELECT r.license_num, res.business_name, r.rating, r.review_comment, r.review_date
    FROM review r
    JOIN restaurant res USING (license_num)
    WHERE r.username = p_username;
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS update_review;
DELIMITER $$
CREATE PROCEDURE update_review(
    IN p_license_num INT,
    IN p_username VARCHAR(32),
    IN p_comment TEXT,
    IN p_rating ENUM('0','1','2','3','4','5')
)
BEGIN
    UPDATE review
    SET review_comment = p_comment,
        rating = p_rating,
        review_date = CURDATE()
    WHERE license_num = p_license_num AND username = p_username;
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS delete_review;
DELIMITER $$
CREATE PROCEDURE delete_review(
    IN p_license_num INT,
    IN p_username VARCHAR(32)
)
BEGIN
    DELETE FROM review
    WHERE license_num = p_license_num AND username = p_username;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS after_review_update;
DELIMITER $$
CREATE TRIGGER after_review_update
AFTER UPDATE ON review
FOR EACH ROW
BEGIN
    UPDATE restaurant
    SET avg_rating = (
        SELECT AVG(CAST(rating AS DECIMAL))
        FROM review
        WHERE license_num = NEW.license_num
    )
    WHERE license_num = NEW.license_num;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS after_review_delete;
DELIMITER $$
CREATE TRIGGER after_review_delete
AFTER DELETE ON review
FOR EACH ROW
BEGIN
    UPDATE restaurant
    SET review_count = GREATEST(review_count - 1, 0),
        avg_rating = (
            SELECT AVG(CAST(rating AS DECIMAL))
            FROM review
            WHERE license_num = OLD.license_num
        )
    WHERE license_num = OLD.license_num;
END$$
DELIMITER ;

-- sandbox

	SELECT * FROM restaurant;

	-- get_restaurant_locations testing
	CALL get_restaurant_locations;

	SELECT tract_id, 
		COUNT(*) AS violation_count,
		COUNT(DISTINCT restaurant.license_num) AS restaurant_count,
		(COUNT(*) / COUNT(DISTINCT restaurant.license_num)) AS violation_density
		FROM violation_log
			INNER JOIN restaurant USING(license_num)
			INNER JOIN address USING (license_num)
			INNER JOIN land_parcel ON land_parcel.land_parcel_id = address.land_parcel_id
			INNER JOIN census_block USING (block_id)
			INNER JOIN census_block_group USING (block_group_id)
			INNER JOIN census_tract USING (tract_id)
			WHERE tract_id
			GROUP BY tract_id;

	-- total_tract_violations
	SET @tc = 0;
	CALL total_tract_violations('25025010405', @tc);
	SELECT @tc;
	CALL get_each_tract_violations_count();

	SET @tcr = 0;
	CALL total_tract_restaurants('25025010405', @tcr);
	SELECT @tcr;

	SELECT @tc / @tcr AS violations_per_restaurant;

		SELECT COUNT(DISTINCT license_num) FROM violation_log
			INNER JOIN restaurant USING(license_num)
			INNER JOIN address USING (license_num)
			INNER JOIN land_parcel ON land_parcel.land_parcel_id = address.land_parcel_id
			INNER JOIN census_block USING (block_id)
			INNER JOIN census_block_group USING (block_group_id)
			INNER JOIN census_tract USING (tract_id)
			WHERE tract_id = '25025010405';
		
		SELECT DISTINCT license_num, business_name, street_num, city FROM violation_log
			INNER JOIN restaurant USING(license_num)
			INNER JOIN address USING (license_num)
			INNER JOIN land_parcel ON land_parcel.land_parcel_id = address.land_parcel_id
			INNER JOIN census_block USING (block_id)
			INNER JOIN census_block_group USING (block_group_id)
			INNER JOIN census_tract USING (tract_id)
			WHERE tract_id = '25025010405';
			
	SELECT * FROM restaurant WHERE business_name LIKE ('%Dunkin%');
	CALL get_restaurant_violations(18174); -- 41 rows
	SELECT * FROM review WHERE license_num = 18678;
	CALL search_by_name_restaurant('Dunkin'); -- 83 when joined using property_num
    -- 64 when joined using license_num??
	CALL search_by_name_restaurant('Nero');
	-- CALL search_by_name_restaurant('Frosty');
	CALL search_by_name_restaurant('Legal');
	CALL search_by_name_restaurant('Thorntons');
	CALL get_all_restaurants_search_options;
	CALL search_by_name_restaurant('Williams'); -- 0
	SELECT business_name, street_num, city FROM restaurant
		INNER JOIN address USING (property_id)
		WHERE business_name LIKE ('%Sea%');
	SELECT * FROM review WHERE license_num = 76498;
	CALL get_restaurant_violations(18174);
	SET @vc = 0;
	CALL get_restaurant_violations_count(18174, @vc);
	SELECT @vc; -- 41 ( matches CALL get_restaurant_violations(18174) rows )

	SELECT violation_level, COUNT(*) as count
	FROM violation_key
	GROUP BY violation_level
	ORDER BY count DESC;

	SELECT * FROM restaurant;