SELECT
    i.__row_id,
    STDEV(t.numMPerfFlatGrosslm) AS stddev_numMperfFlatGross1m_neg_sinceinc,
    COUNT(*) AS count_nummperfflatgrosslm_neg_sinceinc
FROM  t
JOIN #input i ON
    t.strFrequencyCalc = i.strFrequencyCalc
AND t.strDataSource = i.strDataSource
AND t.numPortfGroupFkey = i.numPortfGroupFkey
AND t.numCurrencyIdFKey = i.numCurrencyIdFKey
AND t.numBenchMarkFkey = i.numBenchMarkFkey
AND t.numRiskFreeFKey = i.numRiskFreeFKey
AND t.datNavDate <= i.datNavDate
AND t.datNavDate >= i.StartCalculationDate
AND t.numMPerfFlatGrosslm < 0
GROUP BY i.__row_id


SELECT
    i.__row_id,
    MonthBenchNeg.datNavDate AS Date_24Bench_M
FROM #input i
CROSS APPLY (
    SELECT datNavDate
    FROM (
        SELECT
            t.datNavDate,
            RANK() OVER (ORDER BY t.datNavDate) AS MonthBenchNegNumber
        FROM  t
        WHERE t.numMBenchPerfFlat1m < 0
          AND t.numPortfGroupFkey = i.numPortfGroupFkey
          AND t.numBenchMarkFkey = i.numBenchMarkFkey
          AND t.strDataSource = i.strDataSource
          AND t.numCurrencyIdFKey = i.numCurrencyIdFKey
          AND t.numRiskFreeFKey = i.numRiskFreeFKey
          AND t.strFrequencyCalc = 'M'
    ) MonthBenchNeg
    WHERE MonthBenchNeg.MonthBenchNegNumber = 24
) MonthBenchNeg
