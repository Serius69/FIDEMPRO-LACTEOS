import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-change',
  templateUrl: './change.component.html'
})
export class ChangeComponent{

  StudentArray : any[] = [];
 
  name: string ="";
  address: string ="";
  fee: Number =0;
  description: string ="";
 
  currentStudentID = "";
 
  constructor(private http: HttpClient )
  {
    this.getAllStudent();
  }
 
  saveRecords()
  {
  
    let bodyData = {
      "name" : this.name,
      "address" : this.address,
      "fee" : this.fee
    };
 
    this.http.post("http://127.0.0.1:8000/product/new",bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Student Registered Successfully");
        this.getAllStudent();
    });
  }
 
 
  getAllStudent()
  {
    this.http.get("http://127.0.0.1:8000/product/getall")
    .subscribe((resultData: any)=>
    {
        console.log(resultData);
        this.StudentArray = resultData;
    });
  }
 
 
  setUpdate(data: any)
  {
   this.name = data.name;
   this.address = data.address;
   this.fee = data.fee;
   this.currentStudentID = data.id;
   
  }
 
 
 
  UpdateRecords()
  {
    let bodyData = 
    {
      "name" : this.name,
      "address" : this.address,
      "fee" : this.fee
    };
    
    this.http.put("http://127.0.0.1:8000/student/"+ this.currentStudentID , bodyData).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Student Registered Updateddd")
        this.name = '';
        this.address = '';
        this.fee  = 0;
        this.getAllStudent();
    });
  }


  setDelete(data: any)
  {
    this.http.delete("http://127.0.0.1:8000/student"+ "/"+ data.id).subscribe((resultData: any)=>
    {
        console.log(resultData);
        alert("Student Deletedddd")
        this.getAllStudent();
    });
 
  }

}
