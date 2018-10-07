class Base {
public:
  int public_member;

protected:
  int protected_member;

private:
  int private_member;
};

class Derived : Base {
  void method() {
     public_member;
     protected_member;
     private_member;
  }
};
