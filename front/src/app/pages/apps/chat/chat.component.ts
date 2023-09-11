import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { UntypedFormBuilder, Validators, UntypedFormGroup } from '@angular/forms';
import { GroupUser, ChatUser, ChatMessage, ContactModel } from './chat.model';
import { groupData, chatData, chatMessagesData, contactData } from './data';
import { NgbOffcanvas } from '@ng-bootstrap/ng-bootstrap';

// Date Format
import {DatePipe} from '@angular/common';

// Light Box
import { Lightbox } from 'ngx-lightbox';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.scss']
})

/**
 * Chat Component
 */
export class ChatComponent implements OnInit {
  searchText :any;
  searchMsgText:any;
  chatData!: ChatUser[];
  groupData!: GroupUser[];
  chatMessagesData!: ChatMessage[];
  contactData!: ContactModel[];
  formData!: UntypedFormGroup;
  usermessage!: string;
  isFlag: boolean = false;
  submitted = false;
  isStatus: string = 'online';
  isProfile: string = 'assets/images/users/avatar-2.jpg';
  username: any = 'Lisa Parker';
  @ViewChild('scrollRef') scrollRef:any;
  images: { src: string; thumb: string; caption: string }[] = [];
  isreplyMessage = false;
  emoji = '';

  constructor(public formBuilder: UntypedFormBuilder, private lightbox: Lightbox, private datePipe: DatePipe, private offcanvasService: NgbOffcanvas) { 
    for (let i = 1; i <= 24; i++) {
      const src = '../../../../assets/images/small/img-' + i + '.jpg';
      const caption = 'Image ' + i + ' caption here';
      const thumb = '../../../../assets/images/small/img-' + i + '-thumb.jpg';
      const item = {
        src: src,
        caption: caption,
        thumb: thumb
      };
      this.images.push(item);
    }
  }

  ngOnInit(): void {
    // Chat Data Get Function
    this._fetchData();

    // Validation
    this.formData = this.formBuilder.group({
      message: ['', [Validators.required]],
    });

    // Chat Data Get Function
    this._fetchData();

    this.onListScroll();
  }



  ngAfterViewInit() {
    this.scrollRef.SimpleBar.getScrollElement().scrollTop = 300;
    this.onListScroll();
  }

  // Chat Data Fetch
  private _fetchData() {
    this.groupData = groupData;
    this.chatData = chatData;
    this.chatMessagesData = chatMessagesData;
    this.contactData = contactData;    
  }

  /**
   * Returns form
   */
   get form() {
    return this.formData.controls;
  }

  onListScroll() {
    console.log('vghnbhj', this.scrollRef)
    if (this.scrollRef !== undefined) {
      setTimeout(() => {
        this.scrollRef.SimpleBar.getScrollElement().scrollTop = this.scrollRef.SimpleBar.getScrollElement().scrollHeight;
      }, 500);
    }
  }

  /**
   * Save the message in chat
   */
   messageSave() {
     const message = this.formData.get('message')!.value;  
     if (this.isreplyMessage == true) {
      var itemReplyList:any = document.getElementById("users-chat")?.querySelector(".chat-conversation-list");
      var dateTime = this.datePipe.transform(new Date(),"h:mm a");
      var chatReplyUser = (document.querySelector(".replyCard .replymessage-block .flex-grow-1 .conversation-name") as HTMLAreaElement).innerHTML;
      var chatReplyMessage = (document.querySelector(".replyCard .replymessage-block .flex-grow-1 .mb-0")as HTMLAreaElement).innerText;
  
      this.chatMessagesData.push({
        align: 'right',
        name: 'Marcus',
        replayName: chatReplyUser,
        replaymsg: chatReplyMessage,
        message,
        time: dateTime,
      });
      this.onListScroll();
  
    // Set Form Data Reset
    this.formData = this.formBuilder.group({
      message: null,
    });
    this.isreplyMessage = false;

     }
     else{
      if (this.formData.valid && message) {
        // Message Push in Chat
        this.chatMessagesData.push({
          align: 'right',
          name: 'Marcus',
          message,
          time: this.datePipe.transform(new Date(),"h:mm a"),
        });
        this.onListScroll();
        // Set Form Data Reset
        this.formData = this.formBuilder.group({
          message: null,
        });
      }
    }
    document.querySelector('.replyCard')?.classList.remove('show');
    this.emoji = '';
    
    this.submitted = true;
  }

  /***
  * OnClick User Chat show
  */
  chatUsername(name: string, profile: any, status: string) {
    this.isFlag = true;
    this.username = name;
    const currentDate = new Date();
    this.isStatus = status;
    this.isProfile = profile ? profile : 'assets/images/users/user-dummy-img.jpg';
    this.chatMessagesData.map((chat) => { if (chat.profile) { chat.profile = this.isProfile } });
    const userChatShow = document.querySelector('.user-chat');
    if(userChatShow != null){
      userChatShow.classList.add('user-chat-show');
    }
  }

  open(index: number): void {
    // open lightbox
    this.lightbox.open(this.images, index, { });
  }

  close(): void {
    // close lightbox programmatically
    this.lightbox.close();
  }

 // Copy Message
 copyMessage(event:any){
  navigator.clipboard.writeText(event.target.closest('.chat-list').querySelector('.ctext-content').innerHTML);
  (document.getElementById("copyClipBoard") as HTMLElement).style.display = "block";
  setTimeout(() => {
  (document.getElementById("copyClipBoard") as HTMLElement).style.display = "none";
  }, 1000);
}

  // Delete Message
  deleteMessage(event:any){
    event.target.closest('.chat-list').remove();
  }

  // Replay Message
  replyMessage(event:any,align:any){
    this.isreplyMessage = true;
    document.querySelector('.replyCard')?.classList.add('show');
    var copyText = event.target.closest('.chat-list').querySelector('.ctext-content').innerHTML;
    (document.querySelector(".replyCard .replymessage-block .flex-grow-1 .mb-0") as HTMLAreaElement).innerHTML = copyText;
    var msgOwnerName:any = event.target.closest(".chat-list").classList.contains("right") == true ? 'You' : document.querySelector('.username')?.innerHTML;
    (document.querySelector(".replyCard .replymessage-block .flex-grow-1 .conversation-name") as HTMLAreaElement).innerHTML = msgOwnerName;
  }

  closeReplay(){
    document.querySelector('.replyCard')?.classList.remove('show');
  }

  // Delete All Message
  deleteAllMessage(event:any){
    var allMsgDelete:any = document.getElementById('users-conversation')?.querySelectorAll('.chat-list');
    allMsgDelete.forEach((item:any)=>{
      item.remove();
    })
  }
  

  // Contact Search
  ContactSearch(){
    var input:any, filter:any, ul:any, li:any, a:any | undefined, i:any, txtValue:any;
    input = document.getElementById("searchContact") as HTMLAreaElement;
    filter = input.value.toUpperCase();
    ul = document.querySelectorAll(".chat-user-list");
    ul.forEach((item:any)=>{
      li = item.getElementsByTagName("li");
      for (i = 0; i < li.length; i++) {
        a = li[i].getElementsByTagName("p")[0];
        txtValue = a?.innerText;
        if (txtValue?.toUpperCase().indexOf(filter) > -1) {
          li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
      }
    })
    
  }

  // Message Search
  MessageSearch(){
    var input:any, filter:any, ul:any, li:any, a:any | undefined, i:any, txtValue:any;
    input = document.getElementById("searchMessage") as HTMLAreaElement;
    filter = input.value.toUpperCase();
    ul = document.getElementById("users-conversation");
    li = ul.getElementsByTagName("li");
    for (i = 0; i < li.length; i++) {
      a = li[i].getElementsByTagName("p")[0];
      txtValue = a?.innerText;
      if (txtValue?.toUpperCase().indexOf(filter) > -1) {
        li[i].style.display = "";
    } else {
        li[i].style.display = "none";
    }
    }
  }

  //  Filter Offcanvas Set
  openEnd(content: TemplateRef<any>) {    
    this.offcanvasService.open(content, { position: 'end' });
  }


  // Emoji Picker
  showEmojiPicker = false;
  sets:any = [
    'native',
    'google',
    'twitter',
    'facebook',
    'emojione',
    'apple',
    'messenger'
  ]
  set:any = 'twitter';
  toggleEmojiPicker() {
    this.showEmojiPicker = !this.showEmojiPicker;
  }

  addEmoji(event:any) {
    const { emoji } = this;
    const text = `${emoji}${event.emoji.native}`;
    this.emoji = text;
    this.showEmojiPicker = false;
  }

  onFocus() {
    this.showEmojiPicker = false;
  }
  onBlur() {
  }

  /**
   * Delete Chat Contact Data 
   */
  delete(event:any) {
    event.target.closest('li')?.remove();
  }

  hideChat(){
    const userChatShow = document.querySelector('.user-chat');
    if(userChatShow != null){
      userChatShow.classList.remove('user-chat-show');
    }
  }

}
