<?php
    // The code below is based on what I wrote for my previous games. It still needs modifications.
    include 'config/config.php';
    $conn = mysql_connect($dbhost, $dbuser, $dbpass);

    // Non-standard user agent to disallow simple access via a browser
    $agent = $_SERVER['HTTP_USER_AGENT'];

    if (! $conn ) {
        die('Could not connect: ' . mysql_error());
    }

    $action = $_GET['action'];
    $pname = $_GET['pname'];
    $ppswd = $_GET['ppswd'];
    $ps0 = $_GET['ps0'];
    $ps1 = $_GET['ps1'];
    $ps2 = $_GET['ps2'];
    $ps3 = $_GET['ps3'];
    $ps4 = $_GET['ps4'];
    $ps5 = $_GET['ps5'];
    $plimit = $_GET['plimit'];

    if ($action != 'display') {
        if ($pname == "" or $ppswd == "") {
            die("data_missing");
        }
    }

	mysql_select_db($dbname);

    if($action == 'login') {
   	
   	    if($agent != $vagent) {
			// die("access_denied");
   	    }

		// Check if user exists and password ok
        $sql = "SELECT * FROM players WHERE pname = '$pname' AND ppswd = '$ppswd'";
   	    $result = mysql_query( $sql, $conn );

   	    if (mysql_num_rows($result) > 0) {
   		
            // player & password ok, update last access timestamp
            $sql = "UPDATE players SET placcess=current_timestamp WHERE pname = '$pname' AND ppswd = '$ppswd'";
            $res = mysql_query( $sql, $conn );

            if($result) {
                $sql = "SELECT pname, ps0, ps1, ps2, ps3, ps4, ps5, placcess FROM players WHERE pname = '$pname' AND ppswd = '$ppswd'";
                $result = mysql_query( $sql, $conn );

                if($result) {

                    $row = mysql_fetch_row($result);
                    $pname = $row[0];
                    $ps0 = $row[1];
                    $ps1 = $row[2];
                    $ps2 = $row[3];
                    $ps3 = $row[4];
                    $ps4 = $row[5];
                    $ps5 = $row[6];
                    $placcess = $row[7];

                    echo "login_ok," .$pname. "," .$ps0. ":"  .$ps1. ":"  .$ps2. ":"  .$ps3. ":"  .$ps4. ":"  .$ps5. "," .$placcess;
                }
            }
	
        } else {

            // Check if at least the user exists
            $sql = "SELECT * FROM players WHERE pname = '$pname'";
            $result = mysql_query( $sql, $conn );

            if (mysql_num_rows($result) > 0) {
                // User exist, wrong password
                die("wrong_pswd");
            } else {
                // User not found
                die("no_such_player");
            }
        }
   	
	} else if ($action == 'update') {
		
		if ($agent != $vagent) {
			// die("access_denied");
   	    }

	    // Check if user exists and password ok
        $sql = "SELECT * FROM players WHERE pname = '$pname' AND ppswd = '$ppswd'";
   	    $result = mysql_query( $sql, $conn );
   	
   	    if ($result) {
   		
   		    // user & password ok, update data & last access timestamp

   		    $sql = "UPDATE players SET ";
   		    if(isset($ps0) && !empty(ps0)){
                $sql .= "ps0 = '$ps0'";
            }
            if(isset($ps1) && !empty(ps1)){
                $sql .= ", ps1 = '$ps1'";
            }
            if(isset($ps2) && !empty(ps2)){
                $sql .= ", ps2 = '$ps2'";
            }
            if(isset($ps3) && !empty(ps3)){
                $sql .= ", ps3 = '$ps3'";
            }
            if(isset($ps4) && !empty(ps4)){
                $sql .= ", ps4 = '$ps4'";
            }
            if(isset($ps5) && !empty(ps5)){
                $sql .= ", ps5 = '$ps5'";
            }
            // $sql .= ", placcess=current_timestamp WHERE pname = '$pname'";
            $sql .= ", placcess=current_timestamp WHERE pname = '$pname'";

   		    $result = mysql_query( $sql, $conn );

   		    if($result) {
				echo "scores_updated";
   		    } else {
   		        echo "no_result";
   		    }
	
   	    } else {
   		    die ("user_data_invalid");
   	    }


	} else if ($action == 'create') {
		
		if($agent != $vagent) {
			die("access_denied");
   	    }
   	
   	    // Check if player exists, die if so
        $sql = "SELECT * FROM players WHERE pname = '$pname'";
   	    $result = mysql_query( $sql, $conn );
   	
   	    if(mysql_num_rows($result) > 0) {
   		    die("player_exists");
   	    }

        // create a player
        $sql = "INSERT INTO players (pname, ppswd)
        VALUES('$pname', '$ppswd')";

   	    $result = mysql_query( $sql, $conn );
   	
   	    if($result) {
   			
   		    echo "player_created";
   			 
   	    } else {
   		    echo "failed_creating";
 		}
   	
	} else if ($action == 'delete') {
		
		if($agent != $vagent) {
			die("access_denied");
   	    }
   	
		$sql = "SELECT pname FROM players WHERE pname = '$pname' AND ppswd = '$ppswd'";		
		$result = mysql_query( $sql, $conn );
		
		$num_rows = mysql_num_rows($result);	
		
		if($num_rows > 0){
			
			$row = mysql_fetch_row($result);
			$pname = $row[0];
			$sql = "DELETE FROM players WHERE pname = '$pname' AND ppswd = '$ppswd'";
			$res = mysql_query( $sql, $conn );
			if($res) {
	   			echo "player_deleted";
	   		} else {
	   			echo "failed_deleting";
	   		}
			
		} else {
			echo "no_player_wrong_pass";
		}
   	
	} else if ($action == 'display'){
		
		if ($plimit == 0){
			$sql = "SELECT * FROM players ORDER BY ppoints DESC, ppoints";
		} else {
			$sql = "SELECT * FROM players ORDER BY ppoints DESC, ppoints LIMIT $plimit";
		}

		$result = mysql_query( $sql, $conn );
		$num_rows = mysql_num_rows($result);
		
		while ($row = mysql_fetch_array($result)) {
			echo $row['pname'].",".$row['ppoints'].",".$row['placcess']."#";
		} 
	
	} else {
		echo "action_unknown";
	}
	mysql_close($conn);
?>