CREATE USER auth_service 
WITH PASSWORD 'auth_password';

CREATE DATABASE showbook_auth 
OWNER auth_service;


CREATE USER user_service 
WITH PASSWORD 'user_password';

CREATE DATABASE showbook_user 
OWNER user_service;


CREATE USER catalog_service 
WITH PASSWORD 'catalog_password';

CREATE DATABASE showbook_catalog 
OWNER catalog_service;


CREATE USER venue_service 
WITH PASSWORD 'venue_password';

CREATE DATABASE showbook_venue 
OWNER venue_service;


CREATE USER inventory_service 
WITH PASSWORD 'inventory_password';

CREATE DATABASE showbook_inventory 
OWNER inventory_service;


CREATE USER booking_service 
WITH PASSWORD 'booking_password';

CREATE DATABASE showbook_booking 
OWNER booking_service;


CREATE USER payment_service 
WITH PASSWORD 'payment_password';

CREATE DATABASE showbook_payment 
OWNER payment_service;


CREATE USER notification_service 
WITH PASSWORD 'notification_password';

CREATE DATABASE showbook_notification 
OWNER notification_service;