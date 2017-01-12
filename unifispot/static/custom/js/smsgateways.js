//------------SMS gateway-----------------
$(document).on('change', '#smsgateway', function(){
    if($('#smsgateway').val()== 'twiliowraper'){
      $('#smsauthkey1-form-group').show();
      $('#smsauthkey2-form-group').show();
      $('#smsauthkey3-form-group').hide();
      $('#label_smsauthkey1').text('ACCOUNT SID');
      $('#label_smsauthkey2').text('AUTH TOKEN');
    }
    else if ($('#smsgateway').val() == 'paypalpro'){
      $('#smsauthkey1-form-group').show();
      $('#smsauthkey3-form-group').show();
      $('#smsauthkey3-form-group').show();
      $('#label_smsauthkey1').text('Client ID');
      $('#label_smsauthkey2').text('Client Secret');                    
      $('#label_smsauthkey3').text('Mode(live/sandbox)');                    
    }else{
      $('#smsauthkey1-form-group').hide();
      $('#smsauthkey2-form-group').hide();
      $('#smsauthkey3-form-group').hide();


    }

});   