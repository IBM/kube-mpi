 /*
  Copyright © 2018 IBM Corporation
 
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
 
     http://www.apache.org/licenses/LICENSE-2.0
 
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

/* C Example */
#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>


int main (int argc, char *argv[])
{
  int rank, size;
  int done;

  printf("called hello\n"); fflush(stdout) ;

  MPI_Init (&argc, &argv);	/* starts MPI */
  MPI_Comm_rank (MPI_COMM_WORLD, &rank);	/* get current process id */
  MPI_Comm_size (MPI_COMM_WORLD, &size);	/* get number of processes */
  printf( "Hello world from %d of %d\n", rank, size); fflush(stdout) ;
  printf( "Hello world\n"); fflush(stdout) ;
  sleep(60);
  MPI_Finalize();
  printf("Goodbye\n") ;

  return 0;
}
