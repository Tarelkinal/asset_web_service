# asset_web_service
The financial and analytical Web Service that allows you to monitor changes in the exchange rate and their impact on investment products

## Repository content
- asset_web_service.py - implementation web service based on flask module
- test_asset_web_service.py - unit tests
- composite_store.py - implementation of assets store using composite disign pattern
- logging.config.yml - logger configuration
- cbr_currency_base_daily.html - shapshot of “daily” page to mock external dependencies in unit tests
- cbr_key_indicators.html - shapshot of “key-indicators” page to mock external dependencies in unit tests
- static and templates - directories contain files to render 404 page

## Application functionality
The application implements the following routes (in all cases, the HTTP request has the GET method):
- Error handler 404 (return the 404 code and the text “This route is not found”) in case of request for a non-existing route
-In case of unavailability cbr.ru, it is necessary to return error 503. For this error, a handler returns the message “CBR service is unavailable”.
- Json API: /cbr/daily -- make a request to the “daily” page and get the exchange rate values in the format {“char_code”: rate}
- Json API: /cbr/key_indicators -- make a request to the page “key-indicators” and get values for the exchange rate of USD, EUR and precious metals.
- /api/asset/add/char_code/name/capital/interest -- add an asset in the currency “char_code” with the name “name”, the amount of capital “capital” and the estimated investment annual return “interest” (as a percentage, written as a fractional number; that is, the number 0.5 can be specified as interest, which will mean 50%). To store all the assets,
application uses the Composite design pattern and the global asset storage (app.bank variable).The request returns the return code 200 and the message “Asset '{name}'
was successfully added”. If an attempt is made to add an asset with the name (name), which already exists in the database, then the system issues a 403 return code.
- Json API: /api/asset/list -- return a list of all available assets, each asset is represented by a list [“char_code”, “name”, “capital”, “interest”] Sorting lists by default (that is, the main role in sorting is played by char_code).
- /api/asset/cleanup -- clear the list of assets. The request returns the return code-200.
- Json API: /api/asset/get?name=name_1&name=name_2 -- return a list of all listed assets, each asset is represented as a list [“char_code”, “name”, “capital”, “interest”]. Sorting lists by default (that is, the main role in sorting is played by char_code).
- Json API: /api/asset/calculate_revenue?period=period_1&period=period_2 -- calculate the estimated investment return for the specified time periods (return the dictionary {“period”: “revenue”}), where for currencies USD, EUR and precious metals make requests to the page “key-indicators”, and the rest from the “daily” page. (The accuracy of the comparison of fractional numbers is 10e-8.)
