import { Component, OnInit, QueryList, ViewChildren, TemplateRef } from '@angular/core';
import { NgbModal, NgbOffcanvas } from '@ng-bootstrap/ng-bootstrap';
import { DecimalPipe } from '@angular/common';
import { Observable } from 'rxjs';
import { UntypedFormBuilder, UntypedFormGroup, FormArray, Validators } from '@angular/forms';

import { teamModel } from './team.model';
import { Team } from './data';

@Component({
  selector: 'app-team',
  templateUrl: './team.component.html',
  styleUrls: ['./team.component.scss']
})

/**
 * Team Component
 */
export class TeamComponent {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  Team!: teamModel[];
  submitted = false;
  teamForm!: UntypedFormGroup;
  term: any;

  constructor(private formBuilder: UntypedFormBuilder, private modalService: NgbModal, private offcanvasService: NgbOffcanvas) { }

  ngOnInit(): void {
    /**
    * BreadCrumb
    */
    this.breadCrumbItems = [
      { label: 'Pages' },
      { label: 'Team', active: true }
    ];

    /**
     * Form Validation
     */
    this.teamForm = this.formBuilder.group({
      _id: [''],
      name: ['', [Validators.required]],
      jobPosition: ['', [Validators.required]],
      projectCount: ['', [Validators.required]],
      taskCount: ['', [Validators.required]]
    });

    // Chat Data Get Function
    this._fetchData();
  }

  // Chat Data Fetch
  private _fetchData() {
    this.Team = Team;
  }

  /**
   * Open modal
   * @param content modal content
   */
  openModal(content: any) {
    this.submitted = false;
    this.teamForm = this.formBuilder.group({
      _id: [''],
      name: [''],
      jobPosition: [''],
      projectCount: [''],
      taskCount: ['']
    })
    this.modalService.open(content, { size: 'md', centered: true });
  }

  /**
  * Form data get
  */
  get form() {
    return this.teamForm.controls;
  }

  /**
  * Save Team
  */
  saveTeam() {
      if (this.teamForm.valid) {
        if (this.teamForm.get('_id')?.value) {
          this.Team = Team.map((order: { id: any; }) => order.id === this.teamForm.get('_id')?.value ? { ...order, ...this.teamForm.value } : order);
          this.modalService.dismissAll();
        } else {
          const id = '10';
          const backgroundImg = 'assets/images/small/img-6.jpg';
          const userImage = null;
          const name = this.teamForm.get('name')?.value;
          const jobPosition = this.teamForm.get('jobPosition')?.value;
          const projectCount = this.teamForm.get('projectCount')?.value;
          const taskCount = this.teamForm.get('taskCount')?.value;
          this.Team.push({
            id,
            backgroundImg,
            userImage,
            name,
            jobPosition,
            projectCount,
            taskCount
          });
          this.modalService.dismissAll()
        }
        this.submitted = true
      }
    }

    // Edit Data
    EditData(content: any, id: any) {
      this.submitted = false;
      this.modalService.open(content, { size: 'md', centered: true });
      var modelTitle = document.querySelector('.modal-title') as HTMLAreaElement;
      modelTitle.innerHTML = 'Edit Members';
      var updateBtn = document.getElementById('addNewMember') as HTMLAreaElement;
      updateBtn.innerHTML = "Update";
      let econtent = this.Team[id];
      this.teamForm.controls['name'].setValue(econtent.name);
      this.teamForm.controls['jobPosition'].setValue(econtent.jobPosition);
      this.teamForm.controls['projectCount'].setValue(econtent.projectCount);
      this.teamForm.controls['taskCount'].setValue(econtent.taskCount);
      this.teamForm.controls['_id'].setValue(econtent.id);
      var coverimg: any = document.getElementById('cover-img');
      coverimg.src = econtent.backgroundImg

      var img: any = document.getElementById('member-img');
      if (econtent.userImage) {
        img.src = econtent.userImage
      } else {
        (document.getElementById("member-img") as HTMLElement).style.display = "block"
      }
    }

    /**
     * Active Toggle navbar
     */
    activeMenu(id: any) {
      document.querySelector('.star_' + id)?.classList.toggle('active');
    }

    /**
    * Delete Model Open
    */
    deleteId: any;
    confirm(content: any, id: any) {
      this.deleteId = id;
      this.modalService.open(content, { centered: true });
    }

    // Delete Data
    deleteData(id: any) {
      document.getElementById('t_' + id)?.remove();
    }

    // View Data Get
    viewDataGet(id: any) {
      var teamData = this.Team.filter((team: any) => {
        return team.id === id;
      });
      var profile_img = teamData[0].userImage ?
        `<img src="` + teamData[0].userImage + `" alt="" class="avatar-lg img-thumbnail rounded-circle mx-auto">` :
        `<div class="avatar-lg img-thumbnail rounded-circle flex-shrink-0 mx-auto fs-20">
        <div class="avatar-title bg-danger-subtle text-danger rounded-circle">`+ teamData[0].name[0] + `</div>
      </div>`
      var img_data = (document.querySelector('.profile-offcanvas .team-cover img') as HTMLImageElement);
      img_data.src = teamData[0].backgroundImg;
      var profile = (document.querySelector('.profileImg') as HTMLImageElement);
      profile.innerHTML = profile_img;
      (document.querySelector('.profile-offcanvas .p-3 .mt-3 h5') as HTMLImageElement).innerHTML = teamData[0].name;
      (document.querySelector('.profile-offcanvas .p-3 .mt-3 p') as HTMLImageElement).innerHTML = teamData[0].jobPosition;
      (document.querySelector('.project_count') as HTMLImageElement).innerHTML = teamData[0].projectCount;
      (document.querySelector('.task_count') as HTMLImageElement).innerHTML = teamData[0].taskCount;
    }

    openEnd(content: TemplateRef<any>) {
      this.offcanvasService.open(content, { position: 'end' });
    }

    // File Upload
    imageURL: string | undefined;
    fileChange(event: any) {
      let fileList: any = (event.target as HTMLInputElement);
      let file: File = fileList.files[0];
      document.getElementById('')
      this.teamForm.patchValue({
        // image_src: file.name
        image_src: 'avatar-8.jpg'
      });
      const reader = new FileReader();
      reader.onload = () => {
        this.imageURL = reader.result as string;
        (document.getElementById('member-img') as HTMLImageElement).src = this.imageURL;
      }
      reader.readAsDataURL(file)
    }

    // File Upload
    bgimageURL: string | undefined;
    bgfileChange(event: any) {
      let fileList: any = (event.target as HTMLInputElement);
      let file: File = fileList.files[0];
      document.getElementById('')
      this.teamForm.patchValue({
        // image_src: file.name
        image_src: 'avatar-8.jpg'
      });
      const reader = new FileReader();
      reader.onload = () => {
        this.bgimageURL = reader.result as string;
        (document.getElementById('cover-img') as HTMLImageElement).src = this.bgimageURL;
      }
      reader.readAsDataURL(file)
    }

  }
