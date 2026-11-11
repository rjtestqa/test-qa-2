# Xacta360 Advanced Query - Site Level

This program is designed to crawl through all projects within the accreditation boudnary, and pull data from every project.  

While recommended for development testing and use case confirmation, it should NOT be leveraged in production, and instead a custom query should be used. 

This should be for demonstration purposes only.  

## Processing

1. Retrieve a list of all project from Xacta
2. Convert the query into an object
3. For each project
  - Retrieve the UUID of the project
  - Post the query to the advanced query endpoint of the target project
  - Save the response json dictionary of that project to a json list
4. Write the json object to a results.json in the results directory.  


## Required Arguments

1. File: In JSON format, the data that is being requested from Xacta
2. Server: An X360 Remote Server must exist and be configured in Xacta.Xchange
