(function () {
  var Message;
  Message = function (arg) {
      if(arg.type=="text"){
        this.text = arg.text, this.message_side = arg.message_side;
        this.draw = function (_this) {
            return function () {
                var $message;
                $message = $($('.message_template').clone().html());
                var data = emojione.toImage(_this.text)
                $message.addClass(_this.message_side).find('.text').html(data);
                $('.messages').append($message);
                return setTimeout(function () {
                    return $message.addClass('appeared');
                }, 0);
            };
        }(this);
        return this;
      }else{
        this.photo = arg.photo, this.message_side = arg.message_side,this.user=arg.user;
        this.draw = function (_this) {
            return function () {
                var $message;
                $message = $($('.message_template').clone().html());
                var newImage = document.createElement('img');
                newImage.src = _this.photo
                newImage.style='max-width:100%';
                console.log(newImage)
                var name = "<p>"+_this.user+"</p>"
                $message.addClass(_this.message_side).find('.text').append(name);
                $message.addClass(_this.message_side).find('.text').append(newImage);
                $('.messages').append($message);
                return setTimeout(function () {
                    return $message.addClass('appeared');
                }, 0);
            };
        }(this);
        return this;
      }
  };
  $(function () {
      var getMessageText, message_side, sendMessage;

// Call Python function, and pass explicit callback function
      getMessageText = function () {
          var $message_input;
          $message_input = $('.message_input');
          $(".emojionearea-editor").empty();
          return $message_input.val();
      };
      sendMessage = function (text,side) {
        if(side=="right"){
          eel.sendCommand(text,"message");  // Call a Python function
        }
          var $messages, message;
          if (text.trim() === '') {
              return;
          }
          $('.message_input').val('');
          $messages = $('.messages');
          message = new Message({
              text: text,
              message_side: side,
              type: "text"
          });
          message.draw();
          return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
      };
      sendPhoto = function(user,data,side){
        if(side=="right"){
          eel.sendPhoto(data,"message");  // Call a Python function
        }
          var $messages, message;
          $('.message_input').val('');
          $messages = $('.messages');
          message = new Message({
              message_side: side,
              type:"photo",
              photo:data,
              user:user
          });
          message.draw();
          return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
        }
      eel.expose(recvMessage);               // Expose this function to Python
       function recvMessage(text) {
           sendMessage(text,"left")
       }
       eel.expose(recvPhoto);
       function recvPhoto(user,data){
         sendPhoto(user,data,"left");
       }
      $('.send_message').click(function (e) {
          return sendMessage(getMessageText(),"right");
      });
      $('.message_input').keyup(function (e) {
          if (e.which === 13) {
              return sendMessage(getMessageText(),"right");
          }
      });

  });
}.call(this));
