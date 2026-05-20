-- Overall insights
CREATE PROC GetSolarDashboard
AS
SELECT
    g.governorate_name,
    AVG(w.ALLSKY_SFC_SW_DWN) AS avg_solar,
    AVG(w.peak_sun_hours) AS avg_peak_hours,
    AVG(a.AQI_Level) AS avg_aqi,
    AVG(a.pollution_solar_penalty_pct) AS pollution_penalty
FROM Weather w
JOIN Air_quality a
ON w.governorate_id = a.governorate_id
AND w.w_date = a.a_Date
JOIN Governorate g
ON g.governorate_id = w.governorate_id
GROUP BY g.governorate_name
ORDER BY avg_solar DESC

GetSolarDashboard
-------------------------------------------------------------------------------------------
-- Governorate Information 
CREATE PROC GetGovernorateInfoByID
    @GovernorateID INT
AS
BEGIN
    SELECT
        g.governorate_name,
        g.latitude,
        g.longitude,
        AVG(a.AQI_Level) AS Avg_AQI,
        AVG(w.ALLSKY_SFC_SW_DWN) AS Avg_Solar_Radiation
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    JOIN Air_quality a
        ON g.governorate_id = a.governorate_id
    WHERE g.governorate_id = @GovernorateID
    GROUP BY
        g.governorate_name,
        g.latitude,
        g.longitude
END

GetGovernorateInfoByID 1
--------------------------------------------------------------------------------------
-- Solar Performance Report
CREATE PROC GetSolarPerformance
    @GovernorateID INT
AS
BEGIN
    SELECT
        g.governorate_name,
        AVG(w.peak_sun_hours) AS Avg_Peak_Hours,
        AVG(w.ALLSKY_SFC_SW_DWN) AS Avg_Solar_Radiation,
        AVG(a.pollution_solar_penalty_pct) AS Pollution_Penalty,
        AVG(w.temp_penalty_pct) AS Temp_Penalty,
        (
            AVG(w.ALLSKY_SFC_SW_DWN) * 0.5 +
            AVG(w.peak_sun_hours) * 0.3 -
            AVG(a.pollution_solar_penalty_pct) * 0.1 -
            AVG(w.temp_penalty_pct) * 0.1
        ) AS Solar_Score
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    JOIN Air_quality a
        ON g.governorate_id = a.governorate_id
    WHERE g.governorate_id = @GovernorateID
    GROUP BY g.governorate_name
END
GetSolarPerformance 1
--------------------------------------------------------------------------
--Weather Analysis Report
CREATE PROC GetWeatherAnalysis
    @GovernorateID INT
AS
BEGIN
    SELECT
        g.governorate_name,
        AVG(w.T2M) AS Avg_Temperature,
        AVG(w.RH2M) AS Avg_Humidity,
        AVG(w.WS2M) AS Avg_WindSpeed,
        AVG(w.ALLSKY_SFC_SW_DWN) AS Avg_Solar_Radiation
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    WHERE g.governorate_id = @GovernorateID
    GROUP BY g.governorate_name
END
GetWeatherAnalysis 1
------------------------------------------------------------------
--Pollution Details Report
CREATE PROC GetPollutionDetails
    @AQILevel INT
AS
BEGIN
    SELECT
        g.governorate_name,
        a.PM10,
        a.PM2_5,
        a.Carbon_Monoxide,
        a.Nitrogen_Dioxide,
        a.health_alert,
        a.AQI_Label
    FROM Air_quality a
    JOIN Governorate g
        ON a.governorate_id = g.governorate_id
    WHERE a.AQI_Level >= @AQILevel
END
GetPollutionDetails 2

------------------------------------------------------------------------------
--Best Solar Governorates Report
CREATE PROC GetBestSolarGovernorates
AS
BEGIN
    SELECT
        g.governorate_name,
        AVG(w.ALLSKY_SFC_SW_DWN) AS Avg_Radiation,
        AVG(w.peak_sun_hours) AS Avg_Peak_Hours,
        AVG(a.AQI_Level) AS Avg_AQI,
        (
            AVG(w.ALLSKY_SFC_SW_DWN) * 0.5 +
            AVG(w.peak_sun_hours) * 0.3 -
            AVG(a.pollution_solar_penalty_pct) * 0.1 -
            AVG(w.temp_penalty_pct) * 0.1
        ) AS Solar_Score
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    JOIN Air_quality a
        ON g.governorate_id = a.governorate_id
    GROUP BY g.governorate_name
    ORDER BY Solar_Score DESC
END
GetBestSolarGovernorates 
----------------------------------------------------------------------------------
--Daily Environmental Report
CREATE PROC GetDailyEnvironmentalReport
    @GovernorateID INT,
    @ReportDate DATE
AS
BEGIN
    SELECT
        g.governorate_name,
        w.T2M,
        w.RH2M,
        w.WS2M,
        a.AQI_Level,
        a.AQI_Label,
        w.ALLSKY_SFC_SW_DWN,
        w.peak_sun_hours
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    JOIN Air_quality a
        ON g.governorate_id = a.governorate_id
        AND w.w_date = a.a_Date
    WHERE g.governorate_id = @GovernorateID
        AND w.w_date = @ReportDate
END
GetDailyEnvironmentalReport 2, '1-1-2003'
----------------------------------------------------------
--High Pollution Areas Report
CREATE PROC GetHighPollutionAreaa
    @Threshold INT
AS
BEGIN
    SELECT
        g.governorate_name,
        AVG(a.AQI_Level) AS Avg_AQI,
        COUNT(*) AS Dangerous_Days
    FROM Air_quality a
    JOIN Governorate g
        ON a.governorate_id = g.governorate_id
    WHERE a.AQI_Level >= @Threshold
    GROUP BY g.governorate_name
    ORDER BY Avg_AQI DESC
END
GetHighPollutionAreas
GetHighPollutionAreaa 5
-------------------------------------------------------------
--Governorate Comparison Report
CREATE PROC GetGovernorateComparison
    @Gov1 INT,
    @Gov2 INT
AS
BEGIN
    SELECT
        g.governorate_name,
        AVG(w.T2M) AS Avg_Temp,
        AVG(a.AQI_Level) AS Avg_AQI,
        AVG(w.ALLSKY_SFC_SW_DWN) AS Avg_Radiation,
        AVG(w.peak_sun_hours) AS Avg_Sun_Hours
    FROM Governorate g
    JOIN Weather w
        ON g.governorate_id = w.governorate_id
    JOIN Air_quality a
        ON g.governorate_id = a.governorate_id
    WHERE g.governorate_id IN (@Gov1, @Gov2)
    GROUP BY g.governorate_name
END
GetGovernorateComparison 2, 3
