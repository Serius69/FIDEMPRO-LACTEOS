import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { UsersService } from 'src/app/services/users.service';
import { User2 } from 'src/app/common/user';
import { User } from 'src/app/common/user';

@Component({
  selector: 'app-profile-settings',
  templateUrl: './profile-settings.component.html',
})
export class ProfileSettingsComponent implements OnInit {
  userId: number = 0;
  user: User = new User(this.userId,'',''); // Initialize user as an empty User object
  loadingUserData = false; // Add a loading indicator

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private usersService: UsersService
  ) {}

  // En ProfileComponent
  ngOnInit(): void {
  const userId = 1; // Reemplaza 123 con el ID del usuario que deseas obtener
  this.usersService.getUser(userId).subscribe((data) => {
    // ...
  });
}

  async loadUserData(): Promise<void> {
    try {
      this.loadingUserData = true; // Set loading indicator to true
      const userData = await this.usersService.getUser(this.userId).toPromise();
      if (userData) {
        this.user = userData as User; // Ensure userData is of type User
      } else {
        // Handle the case where no user data was found
      }
    } catch (error) {
      // Handle errors, e.g., show an error message to the user.
    } finally {
      this.loadingUserData = false; // Set loading indicator to false when done
    }
  }
  
  updateUserData(): void {
    this.usersService.updateUser(this.userId, this.user).subscribe(
      (updatedData) => {
        this.user = updatedData;
        // Perform any actions after the update, such as displaying a success message.
      },
      (error) => {
        // Handle errors, e.g., show an error message to the user.
      }
    );
  }

  deleteUserData(): void {
    this.usersService.deleteUser(this.userId).subscribe(
      () => {
        // Perform any actions after the deletion, such as redirecting to a different page.
        this.router.navigate(['/']);
      },
      (error) => {
        // Handle errors, e.g., show an error message to the user.
      }
    );
  }
}
