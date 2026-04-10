USE food_inspections;


SHOW CREATE TABLE restaurant;
ALTER TABLE restaurant
DROP FOREIGN KEY joins_land_parcel,
DROP COLUMN land_parcel_id;

ALTER TABLE app_user
DROP COLUMN user_password;

ALTER TABLE app_user
MODIFY COLUMN home_city varchar(32) NOT NULL;

ALTER TABLE app_user
MODIFY COLUMN home_state char(2) NOT NULL;

SHOW CREATE TABLE app_user;

ALTER TABLE census_tract
MODIFY COLUMN census_year year NOT NULL;

ALTER TABLE census_block_group
MODIFY COLUMN census_year year NOT NULL;

ALTER TABLE census_block
MODIFY COLUMN census_year year NOT NULL;

ALTER TABLE land_parcel
DROP COLUMN gis_id;

-- verify start state
SHOW CREATE TABLE restaurant;

SELECT * FROM restaurant WHERE property_id IS NULL OR issue_date IS NULL OR business_name IS NULL;

SELECT * FROM restaurant WHERE issue_date = 0;

-- confirmed that all restaurant columns have no nulls
ALTER TABLE restaurant
MODIFY COLUMN property_id int NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN issue_date datetime NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN expiration_date datetime NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN license_status ENUM('active', 'inactive', 'deleted') NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN license_type ENUM('FS', 'FT', 'MFW') NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN business_name varchar(512) NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN legal_owner varchar(256) NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN contact_first varchar(256) NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN contact_last varchar(256) NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN price_level varchar(16) NOT NULL;

ALTER TABLE restaurant
MODIFY COLUMN review_count int NOT NULL;
-- keep average rating nullable
SELECT * FROM restaurant WHERE avg_rating IS NULL; -- many avg_rating are null if no reviews exist


use food_inspections;

SHOW CREATE TABLE review;

SELECT * FROM review;
DROP TABLE review;

CREATE TABLE review(
review_id INT AUTO_INCREMENT PRIMARY KEY,
license_num INT NOT NULL,
username varchar(32) NOT NULL,
review_comment VARCHAR(255) DEFAULT NULL, -- was text now varchar(255) for efficiency and data integrity.
rating enum('0', '1', '2', '3', '4', '5') NOT NULL,
review_date date NOT NULL,
CONSTRAINT joins_app_user_fk FOREIGN KEY (username) REFERENCES app_user(username) ON DELETE RESTRICT ON UPDATE RESTRICT,
CONSTRAINT joins_restaurant_fk FOREIGN KEY (license_num) REFERENCES restaurant(license_num) ON DELETE RESTRICT ON UPDATE RESTRICT
);


-- confirm changes
SHOW CREATE TABLE restaurant;
