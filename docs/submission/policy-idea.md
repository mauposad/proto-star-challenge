### Rolling climate normals for cooling-season planning

**1. What risk did we notice?** Utilities, regulators and cities plan for "normal" weather using
a fixed 30-year average. In every backtest we ran, that average was the wrong baseline for
temperature and cooling: a recent level plus a shared trend cut forecast error by about 9%
(skill 8.7% for temperature, 8.9% for CDD, seven-year tests from 1980, 1995 and 2011). Our
forecast for 2019-2025 puts the average year's CDD above the 1989-2018 normal in **206 of 208
scored cities**, by a median of **+9.7%** (+119 °F-days a year). Eleven cities, including
Chicago and San Diego, move above 1,000 CDD, and eight, including Atlanta, move above 2,000.
Planning from the 30-year normal therefore understates the cooling load almost everywhere, and
the shortfall is largest where cooling was rarely needed before (Seattle: +41%, from a low base).

**2. What would we do, and who would do it?** State public utility commissions should require
utilities to use a **rolling, backtested normal** (recent level plus a trend pooled across
cities, refreshed every year and tested on held-out years the way we did) wherever they now use
a fixed 30-year normal: summer peak-load forecasts, reserve planning and efficiency targets.
Each year the utility publishes the table by city. Where a city's rolling normal crosses a
cooling threshold (1,000 or 2,000 CDD), the city's sustainability office and the utility jointly
fund efficiency and cooling-access programs (heat pumps, cool roofs, shade) ahead of the summer,
targeted with local vulnerability data that this dataset does not contain.

**3. Why is it sustainable?** It costs almost nothing: the method runs on data the agencies
already hold, in minutes, and is open in this repository. Planning for the real load early lets
utilities meet it with efficiency and demand response rather than emergency generation, which is
more expensive and more polluting. Because the normal is re-estimated and re-tested every year,
it corrects itself if warming slows or speeds up, instead of locking in a new fixed number.

*Limits:* forecasts are for airport-area stations, not neighborhoods, and carry the backtest
errors in `code/evidence/`.
