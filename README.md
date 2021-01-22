# asset_web_service
The financial and analytical Web Service that allows you to monitor changes in the exchange rate and their impact on investment products

The application implements the following routes (in all cases, the HTTP request has the GET method):
- Error handler 404 (return the 404 code and the text "This route is not found") in case of request for a non-existing route
-In case of unavailability cbr.ru, it is necessary to return error 503. For this error, a handler returns the message "CBR service is unavailable".
- Json API: /cbr/daily-make a request to the “daily " page and get the exchange rate values in the format {"char_code”: rate}
- Json API: /cbr/key_indicators-make a request to the page “key-indicators” and get values for the exchange rate of USD, EUR and precious metals.


? / api/asset/add/char_code/name/capital/interest (don't forget to
specify the Flask converters) - add an asset in the currency "char_code" with the
name "name", the amount of capital "capital" and the estimated
investment annual return “interest " (as a percentage,
written as a fractional number; that is, the
number 0.5 can be specified as interest, which will mean 50%). To store all the assets,
you will need the Composite design pattern and the global asset
storage (for example, save to the app variable.bank ).
3 The
request should return the return code 200 and the message " Asset '{name}'
was successfully added". If an attempt is made to add an asset with the name
(name), which already exists in the database, then the system should issue
a 403 return code.
? Json API: / api/asset/list-return a list of all available assets,
each asset is represented by a list [“char_code", "name", " capital”,
“interest”] Sorting lists by default (that is, the main
role in sorting is played by char_code).
? / api/asset/cleanup-clear the list of assets. The request must return the
return code-200.
? Json API: /api/asset/get? name=name_1&name=name_2-return a list of
all listed assets, each asset is represented as a list
[“char_code”, “name”, “capital”, “interest”]. Sorting lists by
default (that is, the main role in sorting is played by
char_code).
? Json API: /api/asset/calculate_revenue?period=period_1&period=period_2
- calculate the estimated investment return for the specified time
periods (return the dictionary {"period": "revenue"}), where for currencies

2 You can't filter by the length of the char_code (the tests will also have long names), you can only
use the HTML structure and the specified tag classes to parse the desired values
3 The questions of thread-safe and correct work in the prod through multiprocessing are good, but
go beyond the scope of the current training module. I want to know more about it-write
comments, we will prepare an additional one. materials.

mail-to: study@bigdatateam.org https://bigdatateam.org/python-course

USD, EUR and precious metals make requests to the page
“key-indicators” (otherwise the implementation will be considered
incorrect), and the rest from the “daily " page. (The accuracy of the comparison of
fractional numbers is 10e-8.) Also consider that there may be a ruble
asset.
