{{ config(materialized='view', schema='ANALYTICS') }}
select *
from {{ source('superstore','CUSTOMERS') }}
