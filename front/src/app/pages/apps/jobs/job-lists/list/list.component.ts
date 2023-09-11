import { DecimalPipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';

import { ListModel } from './list.model';
import { JoblistService } from './list.service';
import { UntypedFormBuilder, Validators, UntypedFormGroup, UntypedFormArray, AbstractControl } from '@angular/forms';
import { joblist } from './data';

@Component({
  selector: 'app-list',
  templateUrl: './list.component.html',
  styleUrls: ['./list.component.scss'],
  providers: [JoblistService, DecimalPipe]
})
export class ListComponent implements OnInit {

  // bread crumb items
  breadCrumbItems!: Array<{}>;
  joblists: any;
  portfolioChart: any;

  // Form
  jobData!: UntypedFormGroup;
  submitted = false;

  // Table data
  jobList!: Observable<ListModel[]>;
  total: Observable<number>;
  jobdetail: any;

  constructor(public service: JoblistService,
    public formBuilder: UntypedFormBuilder,
    public modalService: NgbModal) {
    this.jobList = service.countries$;
    this.total = service.total$;
  }

  ngOnInit(): void {
    /**
  * BreadCrumb
  */
    this.breadCrumbItems = [
      { label: 'Jobs' },
      { label: 'Job Lists', active: true }
    ];

    // Validation
    this.jobData = this.formBuilder.group({
      id: [''],
      jobtitle: ['', [Validators.required]],
      name: ['', [Validators.required]],
      jobtype: ['', [Validators.required]],
      experience: ['', [Validators.required]],
      location: ['', [Validators.required]],
      salary: ['', [Validators.required]],
      tags: ['', [Validators.required]],
      description: ['', [Validators.required]]
    });

    // Fetch Data
    setTimeout(() => {
      this.jobList.subscribe(x => {
        this.joblists = Object.assign([], x);
      });
      this.jobdetail = this.joblists[0]
      document.getElementById('elmLoader')?.classList.add('d-none')
      document.getElementById('job-overview')?.classList.remove('d-none')
    }, 1200)

    // Chart Color Data Get Function
    this._portfolioChart('["--vz-info", "--vz-primary", "--vz-danger", "--vz-danger", "--vz-info"]');
  }

  // Chart Colors Set
  private getChartColorsArray(colors: any) {
    colors = JSON.parse(colors);
    return colors.map(function (value: any) {
      var newValue = value.replace(" ", "");
      if (newValue.indexOf(",") === -1) {
        var color = getComputedStyle(document.documentElement).getPropertyValue(newValue);
        if (color) {
          color = color.replace(" ", "");
          return color;
        }
        else return newValue;;
      } else {
        var val = value.split(',');
        if (val.length == 2) {
          var rgbaColor = getComputedStyle(document.documentElement).getPropertyValue(val[0]);
          rgbaColor = "rgba(" + rgbaColor + "," + val[1] + ")";
          return rgbaColor;
        } else {
          return newValue;
        }
      }
    });
  }


  /**
* My Portfolio Chart
*/
  private _portfolioChart(colors: any) {
    colors = this.getChartColorsArray(colors);
    this.portfolioChart = {
      series: [98, 63, 35],
      labels: ["New Application", "Approved", "Rejected"],
      chart: {
        type: "donut",
        height: 300,
      },
      legend: {
        position: 'bottom'
      },
      dataLabels: {
        dropShadow: {
          enabled: false,
        }
      },
      colors: colors
    };
  }

  //View detail
  viewmore(id: any) {
    this.jobdetail = this.joblists[id]
  }

  /**
* Open modal
* @param content modal content
*/
  openModal(content: any) {
    // this.submitted = false;
    this.modalService.open(content, { size: 'lg', centered: true });
  }

  /**
* Returns form
*/
  get form() {
    return this.jobData.controls;
  }

  // tags: any = [];
  createJob() {
    if (this.jobData.valid) {
      if (this.jobData.get('id')?.value) {
        this.joblists = this.joblists.map((data: { id: any; }) => data.id === this.jobData.get('id')?.value ? { ...data, ...this.jobData.value } : data)
        // this.service.products = this.applications
      } else {
        const logo = "/assets/images/brands/slack.png";
        const coverimage = "assets/images/small/img-3.jpg";
        const title = this.jobData.get('jobtitle')?.value;
        const companyname = this.jobData.get('name')?.value;
        const content = this.jobData.get('description')?.value;
        const type = this.jobData.get('jobtype')?.value;
        const experience = this.jobData.get('experience')?.value;
        const location = this.jobData.get('location')?.value;
        const applied = '100';
        const date = '26 Sep, 2022';
        const tage = this.jobData.get('tags')?.value;
        const tags = tage.split(',');
        const bookmark = false;
        joblist.push({
          id: this.joblists.length + 1,
          logo,
          coverimage,
          title,
          companyname,
          content,
          type,
          experience,
          location,
          applied,
          date,
          tags,
          bookmark
        });
        this.modalService.dismissAll()
      }
    }
    this.modalService.dismissAll();
    setTimeout(() => {
      this.jobData.reset();
    }, 2000);
    this.submitted = true
  }

  // File Upload
  imageURL: string | undefined;
  fileChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      this.imageURL = reader.result as string;
      document.querySelectorAll('#companylogo-img').forEach((element: any) => {
        element.src = this.imageURL;
      });
    }
    reader.readAsDataURL(file)
  }

  coverURL: string | undefined;
  coverChange(event: any) {
    let fileList: any = (event.target as HTMLInputElement);
    let file: File = fileList.files[0];
    const reader = new FileReader();
    reader.onload = () => {
      this.coverURL = reader.result as string;
      document.querySelectorAll('#modal-cover-img').forEach((element: any) => {
        element.src = this.coverURL;
      });
    }
    reader.readAsDataURL(file)
  }

  bookmarklist(id: any) {
    if (this.joblists[id].bookmark == true) {
      this.joblists[id].bookmark = false
    } else {
      this.joblists[id].bookmark = true
    }
  }

}
