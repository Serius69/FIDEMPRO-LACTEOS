import { Component, OnInit } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

// Ck Editer
import * as ClassicEditor from '@ckeditor/ckeditor5-build-classic';

// Sweet Alert
import Swal from 'sweetalert2';

// Email Data Get
import { emailData } from './data';
import { Email } from './mailbox.model';

@Component({
  selector: 'app-mailbox',
  templateUrl: './mailbox.component.html',
  styleUrls: ['./mailbox.component.scss']
})

/**
 * Mailbox Component
 */
export class MailboxComponent implements OnInit {

  public Editor = ClassicEditor;
  emailData!: Email[];
  emailIds: number[] = [];
  isShowMenu: boolean = true;
  emailDatas: any;
  dataCount: any;
  masterSelected!: boolean;
  cat: any;
  public CcRecipientsCollapse = true;
  public BccRecipientsCollapse = true;

  constructor(private modalService: NgbModal) { }

  ngOnInit(): void {
    /**
     * Fetches the data
     */
    this.fetchData();

    // Compose Model Hide/Show
    var isShowMenu = false;
    document.querySelectorAll(".email-menu-btn").forEach(function (item) {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        isShowMenu = true;
        document.getElementById('menusidebar')?.classList.add("menubar-show");
      });
    });
    document.querySelector('.email-wrapper')?.addEventListener('click', function () {
      if (document.querySelector(".email-menu-sidebar")?.classList.contains('menubar-show')) {
        if (!isShowMenu) {
          document.querySelector(".email-menu-sidebar")?.classList.remove("menubar-show");
        }
        isShowMenu = false;
      }
    });
  }

  /**
   * Fetches the data
   */
  private fetchData() {
    document.getElementById('emaildata')?.classList.add('d-none')
    setTimeout(() => {
      document.getElementById('emaildata')?.classList.remove('d-none')
      this.emailData = emailData;
      this.emailDatas = Object.assign([], this.emailData);
      this.dataCount = this.emailDatas.length
      document.getElementById('elmLoader')?.classList.add('d-none')
    }, 1000);
  }

  /**
  * Open modal
  * @param content content
  */
  open(content: any) {
    this.modalService.open(content, { size: 'lg', centered: true });
  }

  /**
  * on settings button clicked from topbar
  */
  singleData: any = [];
  onSettingsButtonClicked(event: any, id: any) {
    this.singleData = this.emailData.filter((order: any) => {
      return order.id === id;
    });
    this.singleData.forEach((item: any) => {
      this.singleData = item;
    })
    document.body.classList.add('email-detail-show');
  }

  /**
 * Hide the sidebar
 */
  public hide() {
    document.body.classList.remove('email-detail-show');
  }

  /**
   * Confirmation mail model
   */
  confirm(content: any) {
    this.modalService.open(content, { centered: true });
    var checkboxes: any = document.getElementsByName('checkAll');
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < checkboxes.length; i++) {
      if (checkboxes[i].checked) {
        result = checkboxes[i].value;
        checkedVal.push(result);
      }
    }
    this.emailIds = checkedVal
  }

  /***
   * Delete Mail
   */
  deleteData() {
    if (this.emailIds.length > 0) {
      this.emailIds.forEach((item: any) => {
        document.getElementById('chk-' + item)?.remove();
        for (var i = 0; i < this.emailData.length; i++) {
          if (this.emailData[i].id == item) {
            this.emailData[i].category = 'trash'
          }
        }
      });
      (document.getElementById("email-topbar-actions") as HTMLElement).style.display = "none";
    } else {
      for (var i = 0; i < this.emailData.length; i++) {
        if (this.emailData[i].id == this.singleData.id) {
          this.emailData.splice(i, 1)
          this.emailDatas = this.emailData
          document.body.classList.remove('email-detail-show');
        }
      }
    }
  }

  /***
   * send mail select multiple mail
   */
  selectMail(event: any, id: any) {
    var checkboxes: any = document.getElementsByName('checkAll');
    var checkedVal: any[] = [];
    var result
    for (var i = 0; i < checkboxes.length; i++) {
      if (checkboxes[i].checked) {
        result = checkboxes[i].value;
        checkedVal.push(result);
      }
    }
    this.emailIds = checkedVal
    this.emailIds.length > 0 ? (document.getElementById("email-topbar-actions") as HTMLElement).style.display = "block" : (document.getElementById("email-topbar-actions") as HTMLElement).style.display = "none";
  }

  /**
   * Show Mail modal
   * @param content modal content
   */
  showMail() {
    const showMail = document.querySelector('.email-wrapper .email-menu-sidebar');
    if (showMail != null) {
      showMail.classList.add('menubar-show');
    }
  }

  /**
   * SidebarHide modal
   * @param content modal content
   */
  SidebarHide() {
    const recentActivity = document.querySelector('.email-wrapper .email-menu-sidebar');
    if (recentActivity != null) {
      recentActivity.classList.remove('menubar-show');
    }
  }

  // Active Star
  activeStar(id: any, i: any) {
    if (this.emailData[i].category != 'starred') {
      this.cat = this.emailData[i].category
      this.emailData[i].category = 'starred'
    } else {
      this.emailData[i].category = this.cat
    }

    // for (var i = 0; i < this.emailData.length; i++) {
    //   if (id == this.emailData[i].id && this.emailData[i].category != 'starred') {
    //     this.emailData[i].category = 'starred'
    //   }
    //   if (id == this.emailData[i].id) {
    //     this.emailData[i].category = 'all'
    //   }
    // }
    document.querySelector('.star_' + id)?.classList.toggle('active');
  }

  /**
   * Category Filtering  
   */
  categoryFilter(e: any, name: any) {
    var removeClass = document.querySelectorAll('.mail-list a');
    removeClass.forEach((element: any) => {
      element.classList.remove('active');
    });
    e.target.closest('.mail-list a').classList.add('active')
    if (name == 'all') {
      this.emailDatas = this.emailData
    }
    else {
      this.emailDatas = this.emailData.filter((email: any) => {
        return email.category === name;
      });
    }
  }

  /**
   * Label Filtering  
   */
  labelsFilter(e: any, name: any) {
    var removeClass = document.querySelectorAll('.mail-list a');
    removeClass.forEach((element: any) => {
      element.classList.remove('active');
    });
    e.target.closest('.mail-list a').classList.add('active')
    this.emailDatas = this.emailData.filter((email: any) => {
      return email.label === name;
    });
  }

  /**
   * Chat Filtering  
   */
  userName: any
  profile: any = 'user-dummy-img.jpg';
  chatFilter(e: any, name: any, image: any) {
    (document.getElementById("emailchat-detailElem") as HTMLElement).style.display = "block";
    this.userName = name;
    this.profile = image ? image : 'user-dummy-img.jpg';
  }

  // Close Chat
  closeChat() {
    (document.getElementById("emailchat-detailElem") as HTMLElement).style.display = "none";
  }

  // The master checkbox will check/ uncheck all items
  checkUncheckAll(ev: any) {
    this.emailDatas.forEach((x: { state: any; }) => x.state = ev.target.checked)
    if (ev.target.checked) {
      (document.getElementById("email-topbar-actions") as HTMLElement).style.display = "block"
    }
    else {
      (document.getElementById("email-topbar-actions") as HTMLElement).style.display = "none"
    }
  }


}
