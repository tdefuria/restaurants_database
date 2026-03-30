USE food_inspections;

DELIMITER //

DROP PROCEDURE IF EXISTS get_restaurant_count//
CREATE PROCEDURE get_restaurant_count()
BEGIN
    SELECT COUNT(*) FROM restaurant;
END//

DROP PROCEDURE IF EXISTS get_inspection_count//
CREATE PROCEDURE get_inspection_count()
BEGIN
    SELECT COUNT(*) FROM inspection;
END//

DROP PROCEDURE IF EXISTS get_review_count//
CREATE PROCEDURE get_review_count()
BEGIN
    SELECT SUM(review_count) FROM restaurant;
END;

DROP PROCEDURE IF EXISTS get_avg_rating//
CREATE PROCEDURE get_avg_rating()
BEGIN
    SELECT ROUND(AVG(avg_rating), 2) FROM restaurant;
END//

DROP PROCEDURE IF EXISTS get_avg_violations_per_inspection//
CREATE PROCEDURE get_avg_violations_per_inspection()
BEGIN
    SELECT ROUND(AVG(violation_count), 2)
    FROM (
        SELECT COUNT(*) as violation_count
        FROM violation_log
        GROUP BY license_num, result_datetime
    ) counts;
END//

DROP PROCEDURE IF EXISTS get_violations_by_level//
CREATE PROCEDURE get_violations_by_level()
BEGIN
    SELECT violation_level, COUNT(*) as count
    FROM violation_key
    GROUP BY violation_level;
END//

DROP PROCEDURE IF EXISTS get_violations_per_year//
CREATE PROCEDURE get_violations_per_year()
BEGIN
    SELECT YEAR(status_date) as year, COUNT(*) as count
    FROM violation_log
    GROUP BY YEAR(status_date)
    ORDER BY year;
END//

DELIMITER ;
SELECT violation_level, COUNT(*) as count
FROM violation_key
GROUP BY violation_level
ORDER BY count DESC;

SELECT * FROM restaurant;