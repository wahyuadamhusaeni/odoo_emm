###############################################################################
#
#  Vikasa Infinity Anugrah, PT
#  Copyright (C) 2011 - 2012 Vikasa Infinity Anugrah <http://www.infi-nity.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see http://www.gnu.org/licenses/.
#
###############################################################################

_VIA_CURRENCY_CONVERTER_DEF = '''
DECLARE
 last_currency_id BIGINT := NULL;
 last_consolidating_currency_id BIGINT := NULL;
 result NUMERIC := amount;
 rec RECORD;
 conversion_factor NUMERIC;
BEGIN
 IF (amount = 0.0
     OR (SELECT COUNT(*)
         FROM UNNEST(rates_chain)
         WHERE
          level IS NOT NULL
          AND currency_id != consolidating_currency_id) = 0) THEN
  RETURN amount;
 END IF;

 FOR rec IN (SELECT
              rates_link.currency_id AS currency_id,
              rates_link.currency_rates AS currency_rates,
              rates_link.consolidating_currency_id AS consolidating_currency_id,
              rates_link.consolidating_currency_rates AS consolidating_currency_rates
             FROM UNNEST(rates_chain) rates_link
              LEFT JOIN res_currency consolidating_currency
               ON consolidating_currency.id = rates_link.consolidating_currency_id
             WHERE
              level IS NOT NULL
              AND currency_id != consolidating_currency_id
             ORDER BY
              level DESC) LOOP

  IF (last_currency_id = rec.currency_id
      AND last_consolidating_currency_id = rec.consolidating_currency_id) THEN
   CONTINUE;
  END IF;

  SELECT (SELECT rate
          FROM (SELECT DISTINCT * FROM UNNEST(rec.consolidating_currency_rates)) available_rates
          WHERE conversion_date BETWEEN date_start AND COALESCE(date_stop, 'INFINITY'::DATE))
         / (SELECT rate
            FROM (SELECT DISTINCT * FROM UNNEST(rec.currency_rates)) available_rates
            WHERE conversion_date BETWEEN date_start AND COALESCE(date_stop, 'INFINITY'::DATE))
   INTO conversion_factor;

  result := result * COALESCE(conversion_factor, 1.0);

  last_currency_id := rec.currency_id;
  last_consolidating_currency_id := rec.consolidating_currency_id;
 END LOOP;

 RETURN result;
END
'''
