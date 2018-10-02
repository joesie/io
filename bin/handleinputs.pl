#!/usr/bin/perl

use LoxBerry::System;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;
use LoxBerry::IO;
use LoxBerry::Log;
use Time::HiRes qw ( sleep );

my $log = Loxberry::Log::new(name => 'Input handler');

LOGSTART("Daemon gestartet");

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");


#endless loop
while(1){
	for(my $i=0;$i<$pcfg->param("gpios.inputCount");$i++){
		my $gpio= $pcfg->param("inputs.input$i");
	    
	    my $value = system("pigs modes $gpio r");
	    notify( $lbpplugindir, "daemon", "Send value to ms $value");
	    my $response;
	    if($value == 1){
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "input$i", "On");	
	    } else {
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "input$i", "Off");
	    }
	    LOGDEB "Response: $response value: $value";
	    
		if (! $response) {
		    LOGDEB "Error sending to Miniserver";
		} else {
		    LOGDEB "Send ok";
		}
	}
	
	sleep (0.1);
}

exit;
END
{
    if ($log) {
        $log->LOGEND;
    }
}
