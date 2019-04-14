<?php
    include 'config/config.php';
    $conn = mysql_connect($dbhost, $dbuser, $dbpass);
    
    $agent = $_SERVER['HTTP_USER_AGENT'];

    if (! $conn ) {
        die('Could not connect: ' . mysql_error());
    }
    
    if ($agent != $vagent) {
		die("access_denied");
   	}
    
    $plimit = 10;

	mysql_select_db($dbname);

	// associative array: $player_id => $player_penalty_points
	$ascores = array();
		
	// Level0
	$sql = "SELECT pid, pname, ps0 FROM players ORDER BY ps0 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps0'];
		if(isset($score) && !empty($score)){
			// Everyone who passed a level between 2 and 6 must had passed level 1
			// We initiate an associative array here, and update for each next level later
			$ascores[$pid] = ($cnt - 1);  // for 1st position 0 penalty points, for 2nd 1 - and so on
			++$cnt;
		}
	}

	// Level 1
	$sql = "SELECT pid, pname, ps1 FROM players ORDER BY ps1 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps1'];
		// if the player scored on this level
		if(isset($score) && !empty($score)){
			$ascores[$pid] += ($cnt - 1);  // add penalty point according to the player's position
			++$cnt;
		// if the player didn't pass the level
		} else {
			$exists = FALSE;  // skip players w/ no result
			foreach ($ascores as $key => $$value) {
				if ($key == $pid) {
					$exists = TRUE;
				}
			}
			if ($exists == TRUE) {
				$ascores[$pid] += 10;  // add 10 penalty points
			}
		}
	}

	// Level 2
	$sql = "SELECT pid, pname, ps2 FROM players ORDER BY ps2 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$num_rows = mysql_num_rows($result);
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps2'];
		// if the player scored on this level
		if(isset($score) && !empty($score)){
			$ascores[$pid] += ($cnt - 1);  // add penalty point according to the player's position
			++$cnt;
		// if the player didn't pass the level
		} else {
			$exists = FALSE;  // skip players w/ no result
			foreach ($ascores as $key => $$value) {
				if ($key == $pid) {
					$exists = TRUE;
				}
			}
			if ($exists == TRUE) {
				$ascores[$pid] += 10;  // add 10 penalty points
			}
		}
	}

	// Level 3
	$sql = "SELECT pid, pname, ps3 FROM players ORDER BY ps3 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$num_rows = mysql_num_rows($result);
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps3'];
		// if the player scored on this level
		if(isset($score) && !empty($score)){
			$ascores[$pid] += ($cnt - 1);  // add penalty point according to the player's position
			++$cnt;
		// if the player didn't pass the level
		} else {
			$exists = FALSE;  // skip players w/ no result
			foreach ($ascores as $key => $$value) {
				if ($key == $pid) {
					$exists = TRUE;
				}
			}
			if ($exists == TRUE) {
				$ascores[$pid] += 10;  // add 10 penalty points
			}
		}
	}

	// Level 4
	$sql = "SELECT pid, pname, ps4 FROM players ORDER BY ps4 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$num_rows = mysql_num_rows($result);
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps4'];
		// if the player scored on this level
		if(isset($score) && !empty($score)){
			$ascores[$pid] += ($cnt - 1);  // add penalty point according to the player's position
			++$cnt;
		// if the player didn't pass the level
		} else {
			$exists = FALSE;  // skip players w/ no result
			foreach ($ascores as $key => $$value) {
				if ($key == $pid) {
					$exists = TRUE;
				}
			}
			if ($exists == TRUE) {
				$ascores[$pid] += 10;  // add 10 penalty points
			}
		}
	}

	// Level 5
	$sql = "SELECT pid, pname, ps5 FROM players ORDER BY ps5 ASC LIMIT $plimit";
	$result = mysql_query( $sql, $conn );
	$num_rows = mysql_num_rows($result);
	$cnt = 1;
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$score = $row['ps5'];
		// if the player scored on this level
		if(isset($score) && !empty($score)){
			$ascores[$pid] += ($cnt - 1);  // add penalty point according to the player's position
			++$cnt;
		// if the player didn't pass the level
		} else {
			$exists = FALSE;  // skip players w/ no result
			foreach ($ascores as $key => $$value) {
				if ($key == $pid) {
					$exists = TRUE;
				}
			}
			if ($exists == TRUE) {
				$ascores[$pid] += 10;  // add 10 penalty points
			}
		}
	}
	
	// Let's sort in ascending order
	asort($ascores);
	
	// Now we need player names by player id
	$sql = "SELECT pid, pname FROM players WHERE ";
	foreach ($ascores as $key => $value) {
		$sql .= "pid = ".$key." OR ";
	}
	$sql .= "pid = -1";
	$result = mysql_query( $sql, $conn );
	
	$name_by_id = array();
	while ($row = mysql_fetch_array($result)) {
		$pid = $row['pid'];
		$pname = $row['pname'];
		$name_by_id[$pid] = $pname;
	}
	
	$cnt = 1;
	
	$overall = "top_ten#";
	foreach ($ascores as $ascore => $key) {
		$overall .= $cnt.". ".$name_by_id[$ascore]." pen.".$key."#";
		++$cnt;
	}
	echo $overall;
	mysql_close($conn);
?>
