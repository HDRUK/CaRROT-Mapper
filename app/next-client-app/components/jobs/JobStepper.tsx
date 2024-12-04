"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Check, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { StageStatus } from "@/constants/job";

function StepperComponent({ jobGroup }: { jobGroup: Job[] }) {
  // This should be passed as a prop or controlled by parent component
  //   const currentState = ruleActivity; // Example fixed state

  //   const currentIndex = RulesActivities.findIndex(
  //     (step) => step.activity === currentState.activity
  //   );
  //   const currentStatus = ActivityStatus.findIndex(
  //     (step) => step.status === activityStatus.status
  //   );
  //   console.log("🚀 ~ currentStatus:", currentStatus);

  // const renderStepContent = () => {
  //   switch (currentState) {
  //     case 1:
  //       return <ShippingComponent />;
  //     case 2:
  //       return <PaymentComponent />;
  //     case 3:
  //       return <CompleteComponent />;
  //     default:
  //       return null;
  //   }
  // };
  const statusInfo = jobGroup.map((job) =>
    StageStatus.find((option) => option.value === job.status.value)
  );

  return (
    <div className="space-y-6 p-6 rounded-lg w-full">
      <ol
        className="flex items-center justify-between gap-2"
        aria-orientation="horizontal"
      >
        {jobGroup.map((job, index, array) => (
          <React.Fragment key={job.id}>
            <li className="flex flex-col items-center gap-2 flex-shrink-0">
              <Button
                type="button"
                role="tab"
                // aria-current={
                //   currentState.activity === step.activity ? "step" : undefined
                // }
                // aria-posinset={index + 1}
                // aria-setsize={RulesActivities.length}
                // aria-selected={currentState.activity === step.activity}
                className={cn(
                  "flex size-10 items-center justify-center rounded-full bg-carrot text-xl ",
                  StageStatus.find(
                    (option) => option.value === job.status.value
                  )?.color
                )}
              >
                {job.status.value == "COMPLETE" && (
                  <Check className="size-10" />
                )}
                {job.status.value == "IN_PROGRESS" && (
                  <Loader2 className="animate-spin size-10" />
                )}
                {job.status.value == "FAILED" && <X className=" size-10" />}
              </Button>
              <span className="text-sm font-medium">{job.stage.value}</span>
            </li>
            {index < array.length - 1 && (
              <Separator
                className={`flex-1 ${
                  index < job.id ? "bg-carrot" : "bg-muted"
                }`}
              />
            )}
          </React.Fragment>
        ))}
        {/* {jobGroup.map((step, index, array) => (
          <React.Fragment key={step.id}>
            <li className="flex items-center gap-4 flex-shrink-0">
              <Button
                type="button"
                role="tab"
                aria-current={
                  currentState.activity === step.activity ? "step" : undefined
                }
                aria-posinset={index + 1}
                aria-setsize={RulesActivities.length}
                aria-selected={currentState.activity === step.activity}
                className={cn(
                  "flex size-10 items-center justify-center rounded-full bg-carrot-200",
                  index == currentIndex &&
                    currentStatus == 0 &&
                    "bg-yellow-500",
                  index == currentIndex && currentStatus == 1 && "bg-red-500",
                  (index < currentIndex || currentIndex == 4) && "bg-green-500"
                )}
              >
                {(index < currentIndex || currentIndex == 4) && (
                  <Check className="size-5" />
                )}
                {index == currentIndex && currentStatus == 0 && (
                  <Loader2 className="animate-spin size-5" />
                )}
                {index == currentIndex && currentStatus == 1 && (
                  <X className=" size-5" />
                )}
              </Button>
              <span className="text-sm font-medium">{step.activity}</span>
            </li>
            {index < array.length - 1 && (
              <Separator
                className={`flex-1 ${
                  index < currentIndex ? "bg-carrot" : "bg-muted"
                }`}
              />
            )}
          </React.Fragment>
        ))} */}
      </ol>
      {/* <span className="text-sm font-medium">{ruleActivity.activity}</span> */}
      {/* <div className="space-y-4">{renderStepContent()}</div> */}
    </div>
  );
}

// Step Components
const ShippingComponent = () => (
  <div className="grid gap-4">
    <div className="grid gap-2">
      <label htmlFor="name" className="text-sm font-medium text-start">
        Name
      </label>
      <Input id="name" placeholder="John Doe" className="w-full" />
    </div>
    <div className="grid gap-2">
      <label htmlFor="address" className="text-sm font-medium text-start">
        Address
      </label>
      <Textarea
        id="address"
        placeholder="123 Main St, Anytown USA"
        className="w-full"
      />
    </div>
  </div>
);

const PaymentComponent = () => (
  <div className="grid gap-4">
    <div className="grid gap-2">
      <label htmlFor="card-number" className="text-sm font-medium text-start">
        Card Number
      </label>
      <Input
        id="card-number"
        placeholder="4111 1111 1111 1111"
        className="w-full"
      />
    </div>
    <div className="grid grid-cols-2 gap-4">
      <div className="grid gap-2">
        <label htmlFor="expiry-date" className="text-sm font-medium text-start">
          Expiry Date
        </label>
        <Input id="expiry-date" placeholder="MM/YY" className="w-full" />
      </div>
      <div className="grid gap-2">
        <label htmlFor="cvc" className="text-sm font-medium text-start">
          CVC
        </label>
        <Input id="cvc" placeholder="123" className="w-full" />
      </div>
    </div>
  </div>
);

const CompleteComponent = () => (
  <h3 className="text-lg py-4 font-medium">Checkout complete! 🎉</h3>
);

export default StepperComponent;