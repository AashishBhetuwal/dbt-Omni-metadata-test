{{ config(materialized='view') }}

select *
from {{ source('superstore', 'PEOPLE') }}
