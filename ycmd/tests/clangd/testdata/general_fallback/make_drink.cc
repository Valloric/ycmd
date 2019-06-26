#include "make_drink.h"

using namespace Test;

int main( int , char ** )
{
  make_drink( TypeOfDrink::COFFEE, 10.0, Flavour::ELDERFLOWER );
  make_drink( TypeOfDrink::JUICE, Temperature::COLD, 1 );
}
