Our app connects to our SQL server through PyMySQL and provides a UI using Python Shiny Express.
Here is the home page for python shiny express, which you can install to your venv using pip install shiny.
https://shiny.posit.co/blog/posts/shiny-express/
Before you try to install these things manually, consider trying to install our requirements.txt file to save time.

You can find all necessary libraries in the requirements.txt file.
There are a significant number of libraries to ensure your have installed
in your virtual environment, so be sure you have all of them. <br>
To set up your virtual environment:
If you have an existing virtual environment, skip to step 3
to ensure you have all required libraries accessible.  
Step 2 below is for windows powershell users.  
MacOS and Linux users can use bash command "source venv/bin/activate"

1. python -m venv .venv
2. .venv\Scripts\Activate.ps1 <br>
(you must ensure your have activated your virtual environment regardless.)
----------------------------------
3. pip install -r requirements.txt

To run app from terminal: 
- navigate to local folder app.py is located in
- shiny run --reload --launch-browser app.py

You need to have the "Census_2010_Tracts.json" file saved in a "shapes" directory within your project folder.
This contains the shapes for the census tracts used for the app maps, which plot the restaurants.
It automatically reads and loads into the app upon startup.

Here is a breakdown of some package origins included in our requirements.txt file.

| Package/Library           | Source/Purpose                                                                                                                                                                   | 
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| shiny==1.6.0              | this is a default package included when you pip install shiny                                                                                                                    | 
| htmltools==0.6.0          | provides HTML structure where needed within the app                                                                                                                              | 
| uvicorn==0.42.0           | part of default shiny (ASGI server for asynchronous use)                                                                                                                         | 
| starlette==1.0.0          | default shiny                                                                                                                                                                    | 
| asgiref==3.11.1           | default shiny                                                                                                                                                                    | 
| anyio                     | default shiny                                                                                                                                                                    | 
| h11                       | default shiny                                                                                                                                                                    |
| idna                      | default shiny                                                                                                                                                                    | 
| click==8.3.1              | default shiny                                                                                                                                                                    | 
| typing_extensions==4.15.0 | default shiny                                                                                                                                                                    | 
| packaging==26.0           | default shiny                                                                                                                                                                    | 
| shinychat==0.2.9          | default shiny                                                                                                                                                                    | 
| markdown-it-py,           | default shiny                                                                                                                                                                    | 
| mdit-py-plugins,          | default shiny                                                                                                                                                                    |         
| mdurl,                    | default shiny                                                                                                                                                                    |       
| linkify-it-py             | default shiny                                                                                                                                                                    |      
| uc-micro-py               | default shiny                                                                                                                                                                    |
| faicons                   | default shiny                                                                                                                                                                    |
| opentelemetry-api         | default shiny                                                                                                                                                                    | 
| websockets==16.0          | default shiny                                                                                                                                                                    | Required for real-time browser-to-server communication.
| watchfiles==1.1.1         | default shiny                                                                                                                                                                    |  
| python-multipart==0.0.22  | default shiny                                                                                                                                                                    |
| pandas==3.0.1             | converts data to dataframes for plotting & mapping compatibility                                                                                                                 |
| --------------------      | --------------                                                                                                                                                                   | 
| PyMySQL==1.1.2            | make the queries with the sql database                                                                                                                                           |
| cryptography==46.0.6      | Required for pymysql to handle passwords securely. <br> If you do not have there will be an error                                                                                |
| cffi==2.0.0               | Works with cryptography                                                                                                                                                          |
| pycparser==3.0            | Works with cryptography                                                                                                                                                          |
| geopandas==1.1.3          | uses geoDataFrames to add locations for mapping. <br> Ingested the census shapefile needed for the census tract polygons and converted them to geoJSON for plotly compatibility. | 
| shapely==2.1.2            | Handles the geometric shapes (points, lines, polygons)                                                                                                                           |
| pyproj==3.7.2             | Manages map projections and coordinate systems.                                                                                                                                  |
| pyogrio==0.12.1           | A fast interface for reading and writing vector data                                                                                                                             | 
| matplotlib==3.10.8        | plotting tool for the home-page and restaurant-page visualizations                                                                                                               | 
| contourpy                 | Matplotlib.                                                                                                                                                                      |
| cycler                    | Matplotlib.                                                                                                                                                                      |
| fonttools                 | Matplotlib.                                                                                                                                                                      |
| kiwisolver                | Matplotlib.                                                                                                                                                                      |
| pyparsing                 | Matplotlib.                                                                                                                                                                      |
| pillow==12.1.1            | From standard Matplotlib installation Used for image processing (like saving plots as PNGs)                                                                                      |
| python-dateutil & six     | Note: we are running Python version 3.11: General utilities for handling dates and older Python code compatibility                                                               |
| questionary==2.1.1        | Starting the app in the terminal                                                                                                                                                 |  
| prompt_toolkit==3.0.52    | Starting the app in the terminal                                                                                                                                                 | 
| colorama==0.4.6           | Starting the app in the terminal                                                                                                                                                 | 
| wcwidth==0.6.0            | Starting the app in the terminal                                                                                                                                                 |
| narwhals==2.18.1          | default shiny dataframe compatibility                                                                                                                                            |
| tzdata==2025.3            | System/Provides the global timezone database used for date/time calculations.                                                                                                    |
| orjson==3.11.7            | Converting shapefile to JSON/A high-performance JSON library for faster data transfer.                                                                                           |
| certifi==2026.2.25        | A collection of SSL certificates for making secure web requests.                                                                                                                 |
| platformdirs==4.9.4       | Using Python version 3.11/ Helps Python find the correct local system paths for app data.                                                                                        |
| importlib_metadata==8.7.1 | Manages package metadata and entry points.                                                                                                                                       |
| zipp==3.23.0              | A system dependency used by importlib_metadata for reading zip files.                                                                                                            |
