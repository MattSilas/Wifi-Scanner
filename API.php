<?php
//Connect to database
$dbhost = 'your db host';
$dbname = 'your db name';
$dbuser = 'your db user name';
$dbpass = 'your db pass';

$EARTH_RADIUS = 6378000;
$FREQUENCY = 2.4; //In Ghz

ini_set('display_errors', 'On');
$mysql_handle = mysql_connect($dbhost, $dbuser, $dbpass)
or die("Error connecting to database server");
mysql_select_db($dbname, $mysql_handle)
or die("Error selecting database: $dbname");

$el_count = 0; //Counts how many elevation results were found, must be >=4 to find position.


/*
 * Queries the database searching for lat, long, and elevation for a given MAC Address passed in on the QUERY_STRING
 */
function database_query($mysql_handle)
{
	//Parse URL parameters for RSSI and MAC values
	$query = $_SERVER['QUERY_STRING'];
	$vars = array();
	foreach (explode('&', $query) as $pair) {
		list($key, $value) = explode('=', $pair);
		$vars[] = array(urldecode($key), urldecode($value));
	}

	//Variable to iterate 2nd half of array
	$len = count($vars) / 2;

	//Query DB for GPS coordinates
	for($i = 0; $i < count($vars) / 2; $i++)
	{	
		$getLong = mysql_query("SELECT longitude FROM gps_readings WHERE mac_address = '{$vars[$len][1]}'");
		$getLat = mysql_query("SELECT latitude FROM gps_readings WHERE mac_address = '{$vars[$len][1]}'");
		$getEl = mysql_query("SELECT elevation FROM gps_readings WHERE mac_address = '{$vars[$len][1]}'");
		$len++;

		$long = mysql_fetch_array($getLong);
		$lat = mysql_fetch_array($getLat);
		$el = mysql_fetch_array($getEl);

		//Store GPS 
		if($long['longitude'] != NULL && $lat['latitude'] != NULL)
		{
			$wifi_gps_vals[] = array('longitude' => $long['longitude'], 'latitude' => $lat['latitude'], 'RSSI' => $vars[$i][1]);
			if($el['elevation'] !=NULL)
			{
				$wifi_gps_vals[] = array('elevation'=>$el['elevation']);
				$el_count++;
			}
		}
	}
	echo mysql_error();
	mysql_close($mysql_handle);
	return $wifi_gps_vals;
}

$wifi_gps_vals = database_query($mysql_handle);
trilaterate($wifi_gps_vals, $el_count);



/*
 * Checks if the wifi_gps_vals has data.
 * Data are sorted on strongest RSSI by default
 * Calculates GPS based on top 4, 3, 2, or 1 coordinates, based on RSSI
 * Trilaterlates based on weighted average of RSSI
 * Rounds coords to nearest 6th decimal, reducing accuracy by 0.0247 meters, or 0.0008%
 */
function trilaterate($wifi_gps_vals, $el_count){
	if(isset($wifi_gps_vals))
	{
		$sum_rssi =0; //Used to calculate RSSI weighted average
		$user_lat = 0;
		$user_long =0;
		$user_el = 0;

		// Calculate the RSSI sum
		for($i=0; $i<count($wifi_gps_vals)&&$i<4;$i++)
		{
			$sum_rssi = $sum_rssi+ $wifi_gps_vals[$i]['RSSI'];
		}

		//Find latitude based on current position's weighted RSSI average 
		for($i=0; $i<count($wifi_gps_vals)&&$i<4;$i++)
		{
			$user_lat = round($user_lat + ($wifi_gps_vals[$i]['latitude']*($wifi_gps_vals[$i]['RSSI']/$sum_rssi)),6);
		}

		//Find longitude based on current position's weighted RSSI average 
		for($i=0; $i<count($wifi_gps_vals)&&$i<4;$i++)
		{
			$user_long = round($user_long + ($wifi_gps_vals[$i]['longitude']*($wifi_gps_vals[$i]['RSSI']/$sum_rssi)),6);
		}

		//Check for elevation data, if available, calculate elevation based on current position's weighted RSSI average 
		if($el_count>=4)
		{
			for($i=0; $i<count($wifi_gps_vals)&&$i<4;$i++)
			{
			$user_el = $user_el + ($wifi_gps_vals[$i]['elevation']*($wifi_gps_vals[$i]['RSSI']/$sum_rssi));
			}
			$user_cords = array('latitude'=>$user_lat,'longitude'=>$user_long, 'elevation'=>$user_el);	
		}
		else
		{
			$user_cords = array('latitude'=>$user_lat,'longitude'=>$user_long);	
		}	
		echo json_encode($user_cords);		
	}
	else
	{
		echo"{}";
	}
}
// Converts RSSI into meters
function convert_rssi($rssi) {return pow(10,(($rssi-92.45-20*log10($FREQUENCY))/20))*1000;}

// Calculates user's longitude based on distance from wifi access point, 6378000 is Earths radius in meters
function convert_long($converted_rssi, $user_long) {return ($converted_rssi*(2*pi()/360)*$EARTH_RADIUS*cos($user_long));}

// Calculates user's latitude based on distance from wifi access point. 6378000 is Earths radius in meters
function convert_lat($converted_rssi,$user_lat) {return ($converted_rssi *(2*pi()/360)*$EARTH_RADIUS);}

?>
