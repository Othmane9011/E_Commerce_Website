$(document).ready(function(){
  var navbar = $(".nav-user");
  var isVisible = false; 
  var lastScrollTop = 0;

  $(window).scroll(function(){
      var scroll = $(this).scrollTop();

      if (scroll > 500) {
          navbar.css("background" , "#080808");
          
          if (scroll > lastScrollTop && !isVisible) {
              navbar.stop(true, true).fadeIn(500); 
              isVisible = true; 
          } else if (scroll < lastScrollTop && isVisible && scroll < 100) {
              navbar.stop(true, true).fadeOut(500); 
              isVisible = false; 
          }
      } else {
          navbar.css("background" , "transparent");
      }

      lastScrollTop = scroll;
  });
});

