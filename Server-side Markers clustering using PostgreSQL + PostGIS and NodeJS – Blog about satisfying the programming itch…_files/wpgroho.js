WPGroHo=jQuery.extend({my_hash:'',data:{},renderers:{},syncProfileData:function(hash,id){if(!WPGroHo.data[hash]){WPGroHo.data[hash]={};a=jQuery('div.grofile-hash-map-'+hash+' span').each(function(){WPGroHo.data[hash][this.className]=jQuery(this).text();});}
WPGroHo.appendProfileData(WPGroHo.data[hash],hash,id);},appendProfileData:function(data,hash,id){for(var key in data){if(jQuery.isFunction(WPGroHo.renderers[key])){return WPGroHo.renderers[key](data[key],hash,id,key);}
jQuery('#'+id).find('h4').after(jQuery('<p class="grav-extra '+key+'" />').html(data[key]));}}},WPGroHo);
/*
     FILE ARCHIVED ON 21:58:42 Oct 12, 2017 AND RETRIEVED FROM THE
     INTERNET ARCHIVE ON 22:36:17 Dec 22, 2019.
     JAVASCRIPT APPENDED BY WAYBACK MACHINE, COPYRIGHT INTERNET ARCHIVE.

     ALL OTHER CONTENT MAY ALSO BE PROTECTED BY COPYRIGHT (17 U.S.C.
     SECTION 108(a)(3)).
*/
/*
playback timings (ms):
  load_resource: 99.638
  exclusion.robots: 0.201
  LoadShardBlock: 120.239 (6)
  PetaboxLoader3.resolve: 54.819 (2)
  PetaboxLoader3.datanode: 115.031 (8)
  esindex: 0.017
  CDXLines.iter: 95.641 (3)
  RedisCDXSource: 7.132
  exclusion.robots.policy: 0.184
*/